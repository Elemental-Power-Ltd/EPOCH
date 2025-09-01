BEGIN;

DROP INDEX job_queue.job_queue_job_status_bundle_id_idx;
DROP TABLE job_queue.job_status;
DROP SCHEMA job_queue;

END;
