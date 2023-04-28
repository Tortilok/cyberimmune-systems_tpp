SHELL := bash

MODULES := monitor \
		   task-scheduler \
		   update-manager \
		   app-storage \
		   app-updater \
		   app \
		   data-processor-discrete \
		   data-processor-analog \
		   data-storage \
		   scada-receiver \
		   scada-sender \
		   timer \
		   authorization-verifier \
		   license-verifier \
		   command-block \
		   app-receiver \
		   app-sender \
		   app-verifier \
		   data-verifier

SLEEP_TIME := 5

all:
	docker-compose up --build -d
	sleep ${SLEEP_TIME}

	for MODULE in ${MODULES}; do \
		echo Creating $${MODULE} topic; \
		docker exec broker \
			kafka-topics --create --if-not-exists \
			--topic $${MODULE} \
			--bootstrap-server localhost:9092 \
			--replication-factor 1 \
			--partitions 1; \
	done
	
clean:
	docker-compose down
