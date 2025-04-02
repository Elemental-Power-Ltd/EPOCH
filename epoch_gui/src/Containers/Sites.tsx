import {useState} from 'react';
import dayjs, {Dayjs} from "dayjs";
import {Button, CircularProgress, Container, Grid, MenuItem, TextField} from '@mui/material';

import {useEpochStore} from "../State/Store";
import {EpochSiteData} from "../Models/Endpoints";
import {LocalizationProvider} from "@mui/x-date-pickers/LocalizationProvider";
import {AdapterDayjs} from "@mui/x-date-pickers/AdapterDayjs";
import {DateTimePicker} from "@mui/x-date-pickers/DateTimePicker";
import {getLatestSiteData} from "../endpoints";
import {ErrorLoadingSiteData, SiteDataViewer} from "../Components/SiteData/SiteDataViewer";


// A container for viewing information about the different Sites that belong to the client

// There is a large amount of overlap between this and the DatasetGeneration container from a UI perspective
// we're keeping them separate for now as it's simpler but they should be merged into a single tab later.


const SitesContainer = () => {

    const selectedClient = useEpochStore((state) => state.global.selectedClient);
    const sites = useEpochStore((state) => state.global.client_sites);

    const [selectedSite, setSelectedSite] = useState<string>("");

    const [startDate, setStartDate] = useState<Dayjs | null>(dayjs("2022-01-01T00:00:00Z"));
    const [endDate, setEndDate] = useState<Dayjs | null>(dayjs("2023-01-01T00:00:00Z"));

    const [isLoading, setIsLoading] = useState(false);
    const [siteData, setSiteData] = useState<EpochSiteData | null>(null);
    const [error, setError] = useState<String | null>(null);

    const fetchSiteData = async () => {
        setIsLoading(true);
        setError(null);
        setSiteData(null);

        if (!selectedSite || !startDate || !endDate) {
            return
        }

        const siteDataResponse = await getLatestSiteData(selectedSite, startDate, endDate);

        if (siteDataResponse.success) {
           setSiteData(siteDataResponse.data);
        } else {
            setError(siteDataResponse.error || null);
        }
        setIsLoading(false);
    };


    return (
        // we use an 'xl' container as we want the full width of the screen to display graphs within this container
        <Container maxWidth={"xl"}>

            <Container maxWidth={"sm"}>
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <TextField
                            fullWidth
                            select
                            label="Site"
                            value={selectedSite}
                            onChange={(e) => setSelectedSite(e.target.value)}
                            disabled={!selectedClient}
                        >
                            {sites.map((site) => (
                                <MenuItem key={site.site_id} value={site.site_id}>
                                    {site.name}
                                </MenuItem>
                            ))}
                        </TextField>
                    </Grid>
                    <Grid item xs={6}>
                        <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale={"en-gb"}>
                            <DateTimePicker
                                label="Start Date"
                                value={startDate}
                                onChange={(date) => setStartDate(date)}
                            />
                        </LocalizationProvider>
                    </Grid>
                    <Grid item xs={6}>
                        <LocalizationProvider dateAdapter={AdapterDayjs}>
                            <DateTimePicker
                                label="End Date"
                                value={endDate}
                                onChange={(date) => setEndDate(date)}
                            />
                        </LocalizationProvider>
                    </Grid>
                    <Grid item xs={12}>
                        <Button
                            fullWidth
                            variant="contained"
                            color="primary"
                            onClick={fetchSiteData}
                            disabled={!selectedSite || !startDate || !endDate || isLoading}
                        >
                            {isLoading ? <CircularProgress size={24}/> : 'View Site Data'}
                        </Button>
                    </Grid>
                </Grid>
            </Container>

            {error && <ErrorLoadingSiteData/>}
            {siteData && <SiteDataViewer siteData={siteData}/>}
        </Container>
    )
}

export default SitesContainer