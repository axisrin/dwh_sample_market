
# DWH + BI из коробки

Реализация тестового задания в рамках которого был развёрнут DWH в стеке MinIO, PostgeSQL, NiFi, Python (для генерации и автоматизации тестовых данных)

## Маппинг сервисов

NiFi: https://localhost:8443/
(admin/admin123admin123admin123)

Superset: http://localhost:8088/ (admin/admin)

MinIO: http://localhost:9001/ (minioadmin/minioadmin)

PostgeSQL: http://localhost:5432/shop
(etl_user/etl_pass)
## Деплой

1. Первым делом нужно обратить внимание на питоновский файл `main.py`. В нём представлен скрипт генерации данных. Важны строчки:

```bash
clients = generate_clients(20)
merchants = generate_merchants(3)
transactions = generate_transactions(100, clients, merchants)
```

Задайте необходимое значение созданных клиентов, торговых точек и транзакций.

2. Затем в консоли запустите docker-compose.yml

```bash
docker compose up -d
```

3. После успешного запуска у вас будет полностью развёрнутая инфраструктура. Далее необходимо обратить внимание на папку `artifacts`. В папке лежат файлы:

```bash
dashboard_export_20251027T164522.zip (Заготовки для дэша с графиками)

dataset_export_20251027T183623.zip (для быстрого подключения базы данных)

s3_to_postgres_shop_work.json (шаблон для пайплайна загрузки данных в NiFi)
```
4. Заходим в NiFi ( https://localhost:8443/) -> создаём ProcessGroup -> выбираем иконку загрузить из шаблона -> выбираем файл `s3_to_postgres_shop_work.json` и нажимаем Add.

5. Далее заходим в `ProcessGroup` и видим неактивные процессоры, нужно зайти в процессор `ListS3` и во вкладке `Properties` найти строку `AWS Credentials Provider Service`. Справа стоит значение этого свойства и три вертикальные точки. Нажимаем на три точки и выбираем опцию `Go to Service`. Находим наш сервис (начинается он с AWS) и в строке сервиса находим справа три точки, нажимаем и выбираем `Edit`. Видим два свойства `Access Key ID` и `Secret Access Key` , введите в эти свойства `minioadmin`. Нажимаем `Apply`, затем снова на три точки и выбираем `Enable`. Далее так же включаем сервис `CSVReader`. Следующий шаг нажать три точки напротив сервиса `DBCPConnectionPool` и выбрать опцию `Edit`. Нужно найти свойство `Password` и ввести в него `etl_pass`. После чего нажимаем `Apply` и включаем сервис так же, как и предыдущие. 

Возвращаемся в процессор. Необходимо найти первую линию пайп-лайна с названием `Загрузка данных из s3 в postgres` и, начиная с первого блока сверху, нажать правой кнопкой мыши на блок и выбрать `Start`. После всех манипуляций с блоками, в результате работы первого пайплайна у вас будут загружены данные из MinIO в PostgreSQL. 

Находим следующий пайплайн с подписью `Создание таблицы агрегатов`, процесс включения пайплайна аналогичен предыдущему, необходимо включить все блоки, но только здесь уже выполнить включение снизу-вверх, а самый вверхний блок включить выбрав не `Start`, а `Run Once`. В этом блоке выполняется скрипт создания таблицы для аггрегатов :
```SQL
-- 1. Витрина агрегатов
CREATE TABLE IF NOT EXISTS fact_purchase_agg (
    gender        text,                         -- Мужчины / Женщины / NULL (все)
    age_bucket    text,                         -- 'до 18' / '19–30' / 'от 31' / NULL (все)
    industry      text,                         -- индустрия по MCC / NULL (все)
    year          int,                          -- календарный год или NULL (все годы)
    month         int,                          -- 1..12 или NULL (свертка по месяцам)
    sum_purchase  numeric(20,2) NOT NULL,       -- сумма покупок
    avg_purchase  numeric(20,2) NOT NULL,       -- средняя стоимость покупки
    cnt_purchase  bigint        NOT NULL       -- количество покупок
);

-- 2. Индексы под типичные фильтры
CREATE INDEX IF NOT EXISTS ix_fact_agg_time   ON fact_purchase_agg (year, month);
CREATE INDEX IF NOT EXISTS ix_fact_agg_gender ON fact_purchase_agg (gender);
CREATE INDEX IF NOT EXISTS ix_fact_agg_age    ON fact_purchase_agg (age_bucket);
CREATE INDEX IF NOT EXISTS ix_fact_agg_ind    ON fact_purchase_agg (industry);
```

Оставшийся пайплайн запускаем таким же способом, как и предыдущий. В результате отработки пайлайна в базу будут положены рассчитанные данные разложенные геометрически по группировкам. Скрипт для обновления таблицы агрегатов:
```SQL
BEGIN;

TRUNCATE TABLE fact_purchase_agg;

WITH base AS (
  SELECT
      t.transaction_amt::numeric AS amount,
      CASE c.gender WHEN 'M' THEN 'Мужчины' WHEN 'F' THEN 'Женщины' ELSE NULL END AS gender,
      CASE
        WHEN c.age IS NULL THEN NULL
        WHEN c.age <= 18 THEN 'до 18'
        WHEN c.age BETWEEN 19 AND 30 THEN '19–30'
        ELSE 'от 31'
      END AS age_bucket,
      CASE m.mcc_cd
        WHEN 5411 THEN 'Продукты'
        WHEN 5732 THEN 'Электроника'
        WHEN 5812 THEN 'Рестораны'
        WHEN 5921 THEN 'Алкоголь'
        WHEN 5999 THEN 'Прочий ритейл'
        ELSE 'Другое'
      END AS industry,
      EXTRACT(YEAR  FROM t.transaction_dttm)::int AS year,
      EXTRACT(MONTH FROM t.transaction_dttm)::int AS month
  FROM transactions t
  JOIN clients   c ON c.client_id   = t.client_id
  JOIN merchants m ON m.merchant_id = t.merchant_id
)
INSERT INTO fact_purchase_agg
  (gender, age_bucket, industry, year, month, sum_purchase, avg_purchase, cnt_purchase)
SELECT
    gender,
    age_bucket,
    industry,
    year,
    month,
    ROUND(SUM(amount), 2) AS sum_purchase,
    ROUND(AVG(amount), 2) AS avg_purchase,
    COUNT(*)::bigint      AS cnt_purchase
FROM base
GROUP BY
  CUBE (gender, age_bucket, industry),
  GROUPING SETS ((year, month), (year), ());

-- Обновляем статистику для оптимизатора
ANALYZE fact_purchase_agg;

COMMIT;
```

В целом деплой NiFi завершён, можно настроить шедулеры для пайплайнов, но это уже не входило в рамки задания.

6. Перейдём в суперсет (http://localhost:8088/), проходим авторизацию и переходим во вкладку `Datasets`. Справа сверху будет иконка со стрелочкой и окном, нажимем на неё и выбираем из папки `artifacts` файл `dataset_export_20251027T183623.zip`. Нажимаем `import` и нас просят ввести пароль для базы данных. Вводим `etl_pass` и нажимаем `Import`. После импорта датасета, нужно импортировать ещё наш дэш. Открываем вкладку `Dashboards` и так же импортируем файл `dashboard_export_20251027T164522.zip`. После этого появится наш дэш, в котором отрисованы запросы из тестового задания, а так же пару лишних графиков для представления работы витрины.

Скрипты графиков по заданиям:

Сумма вообще всех покупок за 2020 год
```SQL
SELECT sum_purchase AS sum_purchase 
FROM public.fact_purchase_agg 
WHERE year = 2020 AND month IS NULL AND gender IS NULL AND age_bucket IS NULL AND industry IS NULL 
 LIMIT 50000;
```

Сумма всех покупок за апрель 2020 года
```SQL
SELECT 
  sum_purchase AS sum_purchase 
FROM 
  public.fact_purchase_agg 
WHERE 
  year = 2020 
  AND month = 4 
  AND gender IS NULL 
  AND age_bucket IS NULL 
  AND industry IS NULL 
 LIMIT 50000;
```

Сумма покупок всех мужчин за 2020 год
```SQL
SELECT 
  sum_purchase AS sum_purchase 
FROM 
  public.fact_purchase_agg 
WHERE 
  year = 2020 
  AND gender = 'Мужчины' 
  AND industry IS NULL 
  AND month IS NULL 
  AND age_bucket IS NULL 
 LIMIT 50000;
```

Сумма покупок всех мужчин в возрасте 18-31 за 2020 год
```SQL
SELECT 
  sum_purchase AS sum_purchase 
FROM 
  public.fact_purchase_agg 
WHERE 
  gender = 'Мужчины' 
  AND age_bucket = '19–30' 
  AND industry IS NULL 
  AND month IS NULL 
  AND year = 2020 
 LIMIT 50000;
```

Сумма покупок всех женщин за 2020 год
```SQL
SELECT 
  sum_purchase AS sum_purchase 
FROM 
  public.fact_purchase_agg 
WHERE 
  age_bucket IS NULL 
  AND gender = 'Женщины' 
  AND industry IS NULL 
  AND year IN (2020) 
  AND month IS NULL 
 LIMIT 50000;
```

Сумма выручки с разных подразделений по покупательницам 2020 года
```SQL
SELECT 
  industry AS industry, 
  max(sum_purchase) AS "Сумма покупок" 
FROM 
  public.fact_purchase_agg 
WHERE 
  industry IS NOT NULL 
  AND age_bucket IS NULL 
  AND month IS NULL 
  AND year = 2020 
  AND gender = 'Женщины' 
GROUP BY 
  industry 
ORDER BY 
  "Сумма покупок" DESC 
 LIMIT 10000;
```

## Заключение

Спасибо большое за уделённое внимание, надеюсь этот проект покажется вам интересным!


