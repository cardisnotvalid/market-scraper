## Запуск на Windows

- Установка [Python 3.10](https://www.python.org/downloads/release/python-3100/). Не забудьте поставить галочку "Add Python to Path".
- Установить [git](https://git-scm.com/download/win) или напрямую скачать zip файл.

```bash
git clone https://github.com/cardisnotvalid/market-scraper.git
cd market_scraper
```

- Установка требуемых библиотек, запустите `install.bat`

```bash
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
```

- Запуск скрипта через `start.bat`.

## Настройка

Настройки скрипта находятся в `config.yaml`.

```yaml
# -- Filters --
# Фильтры для объявлений
# Дата регистрации продавца
seller_date: [20.05.2013, 20.08.2023]
# Дата создание объявления
ads_date: [20.05.2013, 20.08.2023]
# Количество объявлений продавца
ads_count: 1
# Диапазон цен
price: [0.0, 1000000.0]

# -- Currency --
# Курс CHF валюты в рублях
CHF: 106.68

# -- Developer Settings --
# Отображение дополнительной информации в консоле
debug: True
# Количество потоков
max_concurrent_tasks: 10
```

## Результат

Скрипт сохраняет все объявления в папку `./output`.