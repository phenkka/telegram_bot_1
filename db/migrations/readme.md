How to migrate:

1. Install goose (https://github.com/pressly/goose)
   1. `git clone https://github.com/pressly/goose`
   2. `sudo sh ./goose/install.sh`

2. To run migrations up, in the main project directory run command:
    `goose -dir ./db/migrations/  postgres "user=<USERNAME> dbname=<DB_NAME> sslmode=disable host=<HOST> port=<PORT>" up`

3. To run one migration down run command:
   `goose -dir ./db/migrations/  postgres "user=<USERNAME> dbname=<DB_NAME> sslmode=disable host=<HOST> port=<PORT>" down`
