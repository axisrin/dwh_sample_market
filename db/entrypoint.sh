set -Eeuxo

echo "[db-setup] waiting for postgres..."
until pg_isready -h postgres -U etl_user -d shop >/dev/null 2>&1; do
  echo -n "."
  sleep 1
done

echo
echo "[db-setup] postgres is ready"

echo "[db-setup] check files"
ls -l /ddl.sql || true
head -n 10 /ddl.sql || true

echo "[db-setup] applying DDL to 'shop'..."
psql -v ON_ERROR_STOP=1 -h postgres -U etl_user -d shop -f /ddl.sql

echo "[db-setup] ensure 'superset' DB exists..."
if ! psql -h postgres -U etl_user -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname='superset'" | grep -q 1; then
  psql -h postgres -U etl_user -d postgres -c "CREATE DATABASE superset OWNER etl_user"
  echo "[db-setup] created database 'superset'"
else
  echo "[db-setup] database 'superset' already exists"
fi

echo "[db-setup] done."
