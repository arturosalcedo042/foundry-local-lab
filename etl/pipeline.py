"""Foundry-inspired pipeline: CSV input -> Spark transforms -> Postgres curated tables.
The upsert leaves existing order statuses intact when rerun (operational actions persist).
"""
import os
import psycopg
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import IntegerType, DecimalType

spark = (SparkSession.builder.master("local[2]")
         .appName("foundry-local-lab")
         .config("spark.ui.enabled", "false")
         .config("spark.sql.shuffle.partitions", "2")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
try:
    customers = (spark.read.option("header", True).option("inferSchema", True)
                 .csv("/app/data/customers.csv")
                 .select(F.col("customer_id").cast(IntegerType()).alias("customer_id"),
                         F.trim("name").alias("name"), F.trim("region").alias("region"))
                 .dropDuplicates(["customer_id"]).filter("customer_id IS NOT NULL AND name IS NOT NULL"))
    orders = (spark.read.option("header", True).option("inferSchema", True)
              .csv("/app/data/orders.csv")
              .select(F.col("order_id").cast(IntegerType()).alias("order_id"),
                      F.col("customer_id").cast(IntegerType()).alias("customer_id"),
                      F.col("amount").cast(DecimalType(12, 2)).alias("amount"),
                      F.col("status").alias("status"))
              .dropDuplicates(["order_id"])
              .filter("order_id IS NOT NULL AND customer_id IS NOT NULL AND amount >= 0"))
    payments = (spark.read.option("header", True).option("inferSchema", True)
                .csv("/app/data/payments.csv")
                .select(F.col("order_id").cast(IntegerType()).alias("order_id"),
                        F.col("paid_amount").cast(DecimalType(12, 2)).alias("paid_amount"))
                .groupBy("order_id").agg(F.sum("paid_amount").alias("paid_total")))
    curated = (orders.join(customers.select("customer_id"), "customer_id", "inner")
               .join(payments, "order_id", "left")
               .fillna({"paid_total": 0})
               .withColumn("payment_status", F.when(F.col("paid_total") >= F.col("amount"), "paid")
                           .when(F.col("paid_total") > 0, "partial").otherwise("unpaid"))
               .select("order_id", "customer_id", "amount", "status", "payment_status"))
    customer_rows = [(int(r.customer_id), r.name, r.region) for r in customers.collect()]
    order_rows = [(int(r.order_id), int(r.customer_id), r.amount, r.status, r.payment_status)
                  for r in curated.collect()]
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.executemany("""INSERT INTO customers (customer_id, name, region) VALUES (%s,%s,%s)
                ON CONFLICT (customer_id) DO UPDATE SET name=EXCLUDED.name, region=EXCLUDED.region""", customer_rows)
            cur.executemany("""INSERT INTO orders (order_id, customer_id, amount, status, payment_status)
                VALUES (%s,%s,%s,%s,%s) ON CONFLICT (order_id) DO UPDATE
                SET customer_id=EXCLUDED.customer_id, amount=EXCLUDED.amount,
                    payment_status=EXCLUDED.payment_status""", order_rows)
            cur.execute("""INSERT INTO pipeline_runs (customers_loaded, orders_loaded, result)
                VALUES (%s,%s,'success')""", (len(customer_rows), len(order_rows)))
    print(f"SUCCESS: loaded {len(customer_rows)} customers and {len(order_rows)} orders")
finally:
    spark.stop()
