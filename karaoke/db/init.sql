CREATE DATABASE IF NOT EXISTS `airflow`;
CREATE DATABASE IF NOT EXISTS `celery`;

GRANT ALL PRIVILEGES ON `airflow`.* TO 'airflow'@'%';
GRANT ALL PRIVILEGES ON `celery`.* TO 'airflow'@'%';