name: database-design
description: Schema design, migrations, indexing strategy, query optimization
instructions: |
  When designing database schemas:
  1. Use appropriate types and constraints
  2. Design indexes based on query patterns
  3. Plan zero-downtime migrations
  4. Consider sharding and partitioning for scale
  5. Use EXPLAIN ANALYZE to verify query performance
  Check for: missing indexes, N+1 queries, table scans, lock contention.
