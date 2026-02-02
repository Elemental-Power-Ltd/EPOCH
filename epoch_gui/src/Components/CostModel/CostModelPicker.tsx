import React, {useEffect, useMemo, useState} from "react";
import {
    Alert,
    Box,
    Checkbox,
    CircularProgress,
    FormControl,
    FormControlLabel,
    InputLabel,
    MenuItem,
    Select,
    SelectChangeEvent,
    Stack,
    Typography,
} from "@mui/material";
import dayjs from "dayjs";

import type {CostModelResponse} from "../../Models/Endpoints.ts"
import {listCostModels, getCostModel} from "../../endpoints.tsx";

type Props = {
    costModel: CostModelResponse | null;
    setCostModel: (model: CostModelResponse | null) => void;
};


const sortByCreatedDesc = (a: CostModelResponse, b: CostModelResponse) =>
    dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf();


// remove duplicated Cost Models (apart from unnamed ones)
const dedupeMostRecentByName = (models: CostModelResponse[]): CostModelResponse[] => {
    const seen = new Set<string>();
    const out: CostModelResponse[] = [];
    for (const m of models) {

        const key = m.model_name || "(Unnamed)";
        if (m.model_name !== "(Unnamed)" && seen.has(key)) {
            continue;
        }
        seen.add(key);
        out.push(m);
    }
    return out;
};

export const CostModelPicker: React.FC<Props> = ({costModel, setCostModel}) => {
    const [allModels, setAllModels] = useState<CostModelResponse[]>([]);
    const [hideDuplicates, setHideDuplicates] = useState<boolean>(true);

    const [listLoading, setListLoading] = useState<boolean>(false);
    const [listError, setListError] = useState<string | null>(null);

    const [getLoading, setGetLoading] = useState<boolean>(false);
    const [getError, setGetError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        const run = async () => {
            setListLoading(true);
            setListError(null);

            const res = await listCostModels();
            if (cancelled) return;

            if (!res.success || !res.data) {
                setAllModels([]);
                setListError(res.error ?? "Failed to load cost models.");
            } else {
                // Sort once, store sorted
                setAllModels([...res.data].sort(sortByCreatedDesc));
            }

            setListLoading(false);
        };

        run();

        return () => {
            cancelled = true;
        };
    }, []);

    const visibleModels = useMemo(() => {
        const sorted = [...allModels].sort(sortByCreatedDesc);
        return hideDuplicates ? dedupeMostRecentByName(sorted) : sorted;
    }, [allModels, hideDuplicates]);

    const selectedId = costModel?.cost_model_id ?? "";

    const handleSelect = async (e: SelectChangeEvent<string>) => {
        const id = e.target.value;

        // allow clearing
        if (!id) {
            setCostModel(null);
            setGetError(null);
            return;
        }

        setCostModel(null);
        setGetLoading(true);
        setGetError(null);

        const res = await getCostModel(id);

        if (!res.success || !res.data) {
            setGetError(res.error ?? "Failed to load selected cost model.");
            setGetLoading(false);
            return;
        }

        setCostModel(res.data);
        setGetLoading(false);
    };

    return (
        <Stack spacing={2}>
            <Box>
                <Typography variant="subtitle1">Cost Model</Typography>
                <Typography variant="body2" color="text.secondary">
                    Select a Cost Model
                </Typography>
            </Box>

            <FormControlLabel
                control={
                    <Checkbox
                        checked={hideDuplicates}
                        onChange={(e) => setHideDuplicates(e.target.checked)}
                        disabled={listLoading || !!listError}
                    />
                }
                label="Hide Duplicates"
            />

            {listLoading ? (
                <Box display="flex" alignItems="center" gap={1}>
                    <CircularProgress size={20}/>
                    <Typography variant="body2">Loading cost model…</Typography>
                </Box>
            ) : listError ? (
                <Alert severity="error">{listError}</Alert>
            ) : (
                <FormControl fullWidth>
                    <InputLabel id="cost-model-select-label">Cost Model</InputLabel>
                    <Select
                        labelId="cost-model-select-label"
                        value={selectedId}
                        label="Cost Model"
                        onChange={handleSelect}
                        disabled={visibleModels.length === 0}
                        renderValue={(value) => {
                            if (!value) return "None";
                            const m = allModels.find((x) => x.cost_model_id === value);
                            return m ? `${m.model_name} — ${new Date(m.created_at).toLocaleString()}` : value;
                        }}
                    >
                        <MenuItem value="">
                            <em>None</em>
                        </MenuItem>

                        {visibleModels.map((m) => (
                            <MenuItem key={m.cost_model_id} value={m.cost_model_id}>
                                <Box display="flex" flexDirection="column">
                                    <Typography variant="body1">{m.model_name}</Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        {new Date(m.created_at).toLocaleString()} • {m.cost_model_id}
                                    </Typography>
                                </Box>
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            )}

            {getLoading ? (
                <Box display="flex" alignItems="center" gap={1}>
                    <CircularProgress size={20}/>
                    <Typography variant="body2">Loading selected model…</Typography>
                </Box>
            ) : getError ? (
                <Alert severity="error">{getError}</Alert>
            ) : null}
        </Stack>
    );
};
