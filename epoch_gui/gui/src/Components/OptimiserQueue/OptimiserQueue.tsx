import React from 'react';
import {Card, CardContent, Typography, Grid, Container} from '@mui/material';

import {parseISODuration} from "../../util/displayFunctions";

type TaskState = 'queued' | 'running' | 'cancelled';

interface QueueElem {
    state: TaskState;
    added_at: string;
}

interface OptimiserStatus {
    status: 'OFFLINE' | 'ONLINE';
    queue: { [key: string]: QueueElem };
    service_uptime: string;
}




const QueueElemDisplay: React.FC<{ elem: QueueElem }> = ({elem}) => {
    return (
        <Card variant="outlined" sx={{mb: 2}}>
            <CardContent>
                <Typography variant="h6">State: {elem.state}</Typography>
                <Typography variant="body2">Added At: {new Date(elem.added_at).toLocaleString()}</Typography>
            </CardContent>
        </Card>
    );
};

const QueueList: React.FC<{ queue: { [key: string]: QueueElem } }> = ({queue}) => {
    const isEmpty = Object.keys(queue).length === 0;

    return (
        <Grid container spacing={2}>
            {isEmpty ? (
                <Grid item xs={12}>
                    <Typography variant="h6" align="center">
                        No tasks queued.
                    </Typography>
                </Grid>
            ) : (
                Object.entries(queue).map(([uuid, elem]) => (
                    <Grid item xs={12} key={uuid}>
                        <QueueElemDisplay elem={elem} />
                    </Grid>
                ))
            )}
        </Grid>
    );
};

export const OptimiserStatusDisplay: React.FC<{ status: OptimiserStatus }> = ({status}) => {



    return (
        <Container>
            <Typography variant="h4" gutterBottom>
                Queue Status: {status.status}
            </Typography>
            {status.status === 'ONLINE' &&
                <>
                    <QueueList queue={status.queue}/>
                    <Typography variant="body1" mt={4}>
                        Service Uptime: {parseISODuration(status.service_uptime)}
                    </Typography>
                </>
            }
        </Container>
    );
};

