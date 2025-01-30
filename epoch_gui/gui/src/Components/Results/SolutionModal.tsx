import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Table,
    TableBody,
    TableCell,
    TableRow,
    Typography,
} from '@mui/material';

interface SolutionModalProps {
    open: boolean;
    onClose: () => void;
    solution: { [key: string]: any };
}

const SolutionModal: React.FC<SolutionModalProps> = ({ open, onClose, solution }) => {
    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>Solution Details</DialogTitle>
            <DialogContent dividers>
                <Typography variant="h6" gutterBottom>
                    Solution Parameters
                </Typography>
                <Table>
                    <TableBody>
                        {Object.entries(solution).map(([key, value]) => (
                            <TableRow key={key}>
                                <TableCell>{key}</TableCell>
                                <TableCell>{JSON.stringify(value)}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose} color="primary">
                    Close
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default SolutionModal;
