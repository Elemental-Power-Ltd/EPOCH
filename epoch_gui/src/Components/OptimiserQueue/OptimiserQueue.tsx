import React from 'react';
import {Card, CardContent, Typography, Grid, Container} from '@mui/material';

import {OptimiserStatus, QueueElem} from "../../endpoints.tsx";
import {parseISODuration} from "../../util/displayFunctions.ts";

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
    if (status === 'OFFLINE') {
        return (
            <Container>
                <Typography variant="h4" gutterBottom>
                    Queue Status: OFFLINE
                </Typography>
            </Container>
        )
    }

    return (
        <Container>
            <Typography variant="h4" gutterBottom>
                Queue Status: ONLINE
            </Typography>
            <QueueList queue={status.queue}/>
            <Typography variant="body1" mt={4}>
                Service Uptime: {parseISODuration(status.service_uptime)}
            </Typography>
        </Container>
    );
};

