-- Schema do time-tracker (SQLite, event sourcing simplificado).
--
-- A tabela `time_events` registra a linha do tempo do dia de trabalho.
-- Cada linha e um evento imutavel. O calculo de horas e derivado da sequencia.
--
-- Datas/horas sao guardadas como TEXT em ISO 8601 com offset de timezone
-- (ex: 2026-09-11T09:00:00-03:00), garantindo comparacoes corretas e
-- preservando o fuso. `work_date` e a data local (YYYY-MM-DD).
--
-- Tipos de evento (event_type):
--   START_DAY   -> inicia o dia. task_id = tarefa principal inicial.
--   PAUSE       -> pausa o cronometro. auto_resume_at = horario previsto de retomada.
--   RESUME      -> retoma o cronometro apos uma pausa.
--   CHANGE_TASK -> troca a tarefa principal. task_id = nova tarefa principal.
--   SIDE_TASK   -> lancamento manual de tempo paralelo (code review, reuniao...).
--                  task_id = tarefa da side-task, minutes = tempo gasto.
--   END_DAY     -> finaliza o dia.

CREATE TABLE IF NOT EXISTS time_events (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    work_date      TEXT    NOT NULL,               -- data local YYYY-MM-DD
    event_type     TEXT    NOT NULL CHECK (event_type IN
                       ('START_DAY','PAUSE','RESUME','CHANGE_TASK','SIDE_TASK','END_DAY')),
    task_id        TEXT,                            -- tarefa relacionada (quando aplicavel)
    occurred_at    TEXT    NOT NULL,                -- ISO 8601 com offset
    auto_resume_at TEXT,                            -- PAUSE: quando retomar (ISO 8601)
    minutes        INTEGER,                         -- SIDE_TASK: minutos lancados
    description    TEXT,                            -- descricao livre (SIDE_TASK)
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_time_events_work_date
    ON time_events (work_date, occurred_at);
