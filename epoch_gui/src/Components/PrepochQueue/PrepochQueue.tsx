import React from 'react';
import {Card, CardContent, Typography, Grid, Container} from '@mui/material';
import {PrepochQueueItem, PrepochStatus, PrepochWorkerStatus} from "../../endpoints.tsx";
import dayjs from "dayjs";

const PrepochQueueElemDisplay: React.FC<{ elem: PrepochQueueItem }> = ({elem}) => {
    let subtype_display: string | null = null;

    const subtype = elem.bundle_metadata?.dataset_subtype;
    if (subtype && Array.isArray(subtype)) {
        subtype_display = subtype.join(" • ");
    } else if (subtype) {
        // subtype is a single string
        subtype_display = subtype;
    }

    return (
        <Card variant="outlined" sx={{ mb: 1 }}>
            <CardContent sx={{ py: 1.5 }}>
                <Typography variant="subtitle1">
                    {elem.bundle_metadata?.dataset_type || 'Unknown Task'}
                </Typography>
                {subtype_display ? (
                    <Typography variant="caption" color="text.secondary">
                        {subtype_display}
                    </Typography>
                ) : null}
            </CardContent>
        </Card>
    );
};

const PrepochQueueDisplay: React.FC<{ queue: PrepochQueueItem[] }> = ({ queue }) => {
    const isEmpty = queue.length === 0;

    return (
        <Container sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
                Queued
            </Typography>

            {isEmpty ? (
                <Card variant="outlined">
                    <CardContent sx={{ py: 1.5 }}>
                        <Typography variant="body1" color="text.secondary">
                            No tasks queued
                        </Typography>
                    </CardContent>
                </Card>
            ) : (
                <Grid container spacing={1}>
                    {queue.map((elem, idx) => (
                        <Grid item xs={12} md={6} key={idx}>
                            <PrepochQueueElemDisplay elem={elem} />
                        </Grid>
                    ))}
                </Grid>
            )}
        </Container>
    );
};

const PrepochWorkerCard: React.FC<{ worker: PrepochWorkerStatus }> = ({ worker }) => {
    const isRunning = worker.current_job != null;

    return (
        <Card
            variant="outlined"
            sx={{
                height: "100%",
                borderWidth: 2,
            }}
        >
            <CardContent>
                <Typography variant="overline" color="text.secondary">
                    {worker.name}
                </Typography>

                <Typography variant="h6" sx={{ mt: 0.5 }}>
                    {isRunning ? "Processing" : "Idle"}
                </Typography>

                {isRunning ? (
                    <>
                        <Typography variant="subtitle1" sx={{ mt: 0.5 }}>
                            {worker.current_job}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            Started: {dayjs(worker.started_at).format("HH:mm")}
                        </Typography>
                    </>
                ) : (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        No task in progress
                    </Typography>
                )}
            </CardContent>
        </Card>
    );
};

const PrepochWorkerDisplay: React.FC<{ workers: PrepochWorkerStatus[] }> = ({ workers }) => {
    return (
        <Container sx={{ mb: 2 }}>
            <Typography variant="h5" gutterBottom>
                Workers
            </Typography>

            <Grid container spacing={2}>
                {workers.map((worker) => (
                    <Grid item xs={12} md={6} key={worker.name}>
                        <PrepochWorkerCard worker={worker} />
                    </Grid>
                ))}
            </Grid>
        </Container>
    );
};

export const PrepochStatusDisplay: React.FC<{ status: PrepochStatus }> = ({status}) => {
    if (status === 'OFFLINE') {
        return (
            <Container>
                <Typography variant="h4" gutterBottom>
                    Queue Status: OFFLINE
                </Typography>
            </Container>
        );
    }

    return (
        <Container sx={{mb: 2}}>
            <PrepochWorkerDisplay workers={status.workers}/>
            <PrepochQueueDisplay queue={status.queue}/>
        </Container>
    );
};
