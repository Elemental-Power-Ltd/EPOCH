import {useEffect, useMemo, useState} from "react";
import {
    Alert,
    Button,
    Checkbox,
    CircularProgress,
    Container,
    Dialog,
    DialogContent,
    DialogContentText,
    DialogTitle,
    DialogActions,
    Grid,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableRow,
    Typography,
} from "@mui/material";

import {addFeasibleInterventions, listFeasibleInterventions} from "../../endpoints";
import {IsInterventionFeasible} from "../../Models/Endpoints.ts";

interface FeasibleInterventionsFormProps {
    selectedSite: string;
}

const FeasibleInterventionsForm = ({selectedSite}: FeasibleInterventionsFormProps) => {
    // list-feasible state
    const [options, setOptions] = useState<IsInterventionFeasible[]>([]);
    const [listLoading, setListLoading] = useState(false);
    const [listError, setListError] = useState<string | null>(null);

    // add-feasible state
    const [saveLoading, setSaveLoading] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [saveResult, setSaveResult] = useState<string | null>(null);

    // Track checked items by name
    const [selected, setSelected] = useState<Record<string, boolean>>({});


    const [confirmOpen, setConfirmOpen] = useState<boolean>(false);
    const selectedOptions = options.filter(option => selected[option.name]);
    const requiresConfirmation = selectedOptions.length > 6;
    const submissionDisabledBySize = selectedOptions.length > 8;
    const permutations = 2 ** selectedOptions.length;

    const canSubmit = () => {
        return selectedSite !== "" && !saveLoading && !listLoading && !submissionDisabledBySize;
    }


    const {previouslySelected, previouslyUnselected} = useMemo(() => {
        const previouslySelected: IsInterventionFeasible[] = [];
        const previouslyUnselected: IsInterventionFeasible[] = [];

        for (const opt of options) {
            if (opt.is_feasible) previouslySelected.push(opt);
            else previouslyUnselected.push(opt);
        }

        return {previouslySelected, previouslyUnselected};
    }, [options]);

    const loadOptions = async () => {
        if (!selectedSite) {
            setOptions([]);
            setSelected({});
            setListError(null);
            setSaveResult(null);
            setSaveError(null);
            return;
        }

        setListLoading(true);
        setListError(null);
        setSaveResult(null);

        try {
            const res = await listFeasibleInterventions(selectedSite);

            if (!res.success) {
                setOptions([]);
                setSelected({});
                setListError(res.error ?? "Unknown Error");
                return;
            }

            const data = res.data ?? [];
            setOptions(data);

            const nextSelected: Record<string, boolean> = {};

            for (const item of data) {
                nextSelected[item.name] = item.is_feasible;
            }

            setSelected(nextSelected);
        } catch (e) {
            setOptions([]);
            setSelected({});
            setListError(e instanceof Error ? e.message : "Unknown Error");
        } finally {
            setListLoading(false);
        }
    };

    useEffect(() => {
        void loadOptions();
    }, [selectedSite]);

    const toggle = (name: string) => {
        setSelected((prev) => ({...prev, [name]: !prev[name]}));
    };


    const doSubmit = async () => {
        if (!canSubmit()) return;

        setSaveLoading(true);
        setSaveError(null);
        setSaveResult(null);

        try {
            const interventionsToSet = options
                .map((intervention) => intervention.name)
                .filter((name) => selected[name]);

            const res = await addFeasibleInterventions(selectedSite, interventionsToSet);

            if (!res.success) {
                setSaveError(res.error ?? "Unknown Error");
            } else {
                const countPerms = res.data?.length ?? 0;
                setSaveResult(
                    `Saved ${interventionsToSet.length} intervention(s). Returned ${countPerms} permutation(s).`
                );
            }
        } catch (e) {
            setSaveError(e instanceof Error ? e.message : "Unknown Error");
        } finally {
            setSaveLoading(false);
        }
    };

    const handleSetInterventions = async () => {
        if (!canSubmit()) return;

        if (requiresConfirmation) {
            setConfirmOpen(true);
        } else {
            await doSubmit();
        }
    }

    const checkboxDisabled = listLoading || saveLoading;

    return (
        <Container maxWidth="sm">
            <Typography variant="h5" gutterBottom mt={2}>
                Feasible Interventions
            </Typography>

            <Grid container spacing={2}>
                {listError && (
                    <Grid item xs={12}>
                        <Alert severity="error">{listError}</Alert>
                    </Grid>
                )}

                {saveError && (
                    <Grid item xs={12}>
                        <Alert severity="error">{saveError}</Alert>
                    </Grid>
                )}

                {saveResult && (
                    <Grid item xs={12}>
                        <Alert severity="success">{saveResult}</Alert>
                    </Grid>
                )}

                <Grid item xs={12}>
                    <TableContainer component={Paper} variant="outlined">
                        <Table size="small" aria-label="feasible interventions table">

                            <TableBody>
                                {!listLoading && options.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={2}>
                                            <Typography variant="body2" color="text.secondary">
                                                {selectedSite
                                                    ? "No interventions returned for this site."
                                                    : "Select a site to load interventions."}
                                            </Typography>
                                        </TableCell>
                                    </TableRow>
                                )}

                                {!listLoading && options.length > 0 && (
                                    <>
                                        <TableRow>
                                            <TableCell colSpan={2}>
                                                <Typography variant="h6">Previously Selected</Typography>
                                            </TableCell>
                                        </TableRow>

                                        {previouslySelected.length === 0 ? (
                                            <TableRow>
                                                <TableCell colSpan={2}>
                                                    <Typography variant="body2" color="text.secondary">
                                                        None
                                                    </Typography>
                                                </TableCell>
                                            </TableRow>
                                        ) : (
                                            previouslySelected.map((opt) => (
                                                <TableRow key={opt.name} hover>
                                                    <TableCell>{opt.name}</TableCell>
                                                    <TableCell align="right" padding="checkbox">
                                                        <Checkbox
                                                            checked={!!selected[opt.name]}
                                                            onChange={() => toggle(opt.name)}
                                                            disabled={checkboxDisabled}
                                                            inputProps={{"aria-label": `toggle ${opt.name}`}}
                                                        />
                                                    </TableCell>
                                                </TableRow>
                                            ))
                                        )}

                                        <TableRow>
                                            <TableCell colSpan={2}>
                                                <Typography variant="h6" sx={{mt: 1}}>
                                                    Previously Unselected
                                                </Typography>
                                            </TableCell>
                                        </TableRow>

                                        {previouslyUnselected.length === 0 ? (
                                            <TableRow>
                                                <TableCell colSpan={2}>
                                                    <Typography variant="body2" color="text.secondary">
                                                        None
                                                    </Typography>
                                                </TableCell>
                                            </TableRow>
                                        ) : (
                                            previouslyUnselected.map((opt) => (
                                                <TableRow key={opt.name} hover>
                                                    <TableCell>{opt.name}</TableCell>
                                                    <TableCell align="right" padding="checkbox">
                                                        <Checkbox
                                                            checked={!!selected[opt.name]}
                                                            onChange={() => toggle(opt.name)}
                                                            disabled={checkboxDisabled}
                                                            inputProps={{"aria-label": `toggle ${opt.name}`}}
                                                        />
                                                    </TableCell>
                                                </TableRow>
                                            ))
                                        )}
                                    </>
                                )}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </Grid>

                <Grid item xs={12}>
                    <Button
                        fullWidth
                        variant="contained"
                        color="primary"
                        disabled={!canSubmit()}
                        onClick={handleSetInterventions}
                    >
                        {saveLoading ? <CircularProgress size={24}/> : "Set Interventions"}
                    </Button>
                    {submissionDisabledBySize && (
                        <Typography variant="caption" color="text.secondary" display="block" sx={{mt: 1}}>
                            Maximum of 8 interventions permitted
                        </Typography>
                    )}
                </Grid>
            </Grid>

            <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)} maxWidth="xs" fullWidth>
                <DialogTitle>Confirm submission</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        You have selected <b>{selectedOptions.length}</b> interventions. This will generate {" "}
                        <b>{permutations.toLocaleString()}</b> permutations
                        <br/>
                        <br/>
                        Do you want to continue?
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setConfirmOpen(false)} disabled={saveLoading}>
                        Cancel
                    </Button>
                    <Button
                        onClick={async () => {
                            setConfirmOpen(false);
                            await doSubmit();
                        }}
                        variant="contained"
                        disabled={saveLoading || submissionDisabledBySize}
                    >
                        {saveLoading ? <CircularProgress size={20}/> : "Continue"}
                    </Button>
                </DialogActions>
            </Dialog>


        </Container>
    );
};

export default FeasibleInterventionsForm;
