import React from 'react';
import {Card, CardContent, Typography, Grid, Container} from '@mui/material';

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

const parseISODuration = (duration: string): string => {
    const match = duration.match(/PT([\d\.]+)S/);
    if (!match) return 'Invalid duration';

    const totalSeconds = parseFloat(match[1]);
    const days = Math.floor(totalSeconds / (3600 * 24));
    let seconds = totalSeconds % (3600 * 24);
    const hours = Math.floor(seconds / 3600);
    seconds %= 3600;
    const minutes = Math.floor(seconds / 60);
    seconds %= 60;

    let uptimeString = '';
    if (days > 0) uptimeString += `${days} day${days > 1 ? 's' : ''}, `;
    if (hours > 0) uptimeString += `${hours} hour${hours > 1 ? 's' : ''}, `;
    if (minutes > 0) uptimeString += `${minutes} minute${minutes > 1 ? 's' : ''}, `;
    uptimeString += `${seconds.toFixed(0)} second${seconds !== 1 ? 's' : ''}`;

    return uptimeString;
};


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

