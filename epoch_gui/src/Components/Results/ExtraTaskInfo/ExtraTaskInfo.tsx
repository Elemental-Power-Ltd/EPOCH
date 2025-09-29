import React, {useState} from "react";

import {
    Button,
    Container,
    Dialog,
    DialogTitle,
    DialogContent,
    Tabs,
    Tab,
    Box

} from '@mui/material';
import {SearchSpacesViewer} from "../SearchSpaceViewer.tsx";
import {HintViewer} from "../../Bundles/HintViewer.tsx";
import {BundleHint, SearchSpaces} from "../../../Models/Endpoints.ts";
import {Site} from "../../../State/types";


type TabPanelProps = {
  children: React.ReactNode;
  value: number;
  index: number;
};

function TabPanel({ children, value, index }: TabPanelProps) {
    return (
        <div role="tabpanel" hidden={value !== index}>
            {value === index && <Box sx={{pt: 2}}>{children}</Box>}
        </div>
    );
}

export const ExtraTaskInfo = ({searchSpace, hints, sites}: {
    searchSpace?: SearchSpaces,
    hints: Record<string, BundleHint>,
    sites: Site[]
}) => {


    const [showInfo, setShowInfo] = useState(false);
    const [tab, setTab] = useState(0);

    const getSiteName = (site_id: string) => {
        const site = sites.find(site => site.site_id === site_id);
        return site ? site.name : site_id;
    }


    return (
        <>
            <Button onClick={() => setShowInfo(true)} variant="outlined">More Info</Button>


            <Dialog open={showInfo} onClose={() => {setShowInfo(false)}} maxWidth="xl">
                <DialogTitle>Task Info</DialogTitle>

                <DialogContent>
                    <Tabs value={tab} onChange={(_, newValue) => setTab(newValue)}>
                        <Tab label="Search Space"/>
                        <Tab label="Hints"/>
                    </Tabs>

                    <TabPanel value={tab} index={0}>
                        <Container maxWidth="xl">
                            {searchSpace && (
                                <SearchSpacesViewer data={searchSpace} sites={sites}/>
                            )}
                        </Container>
                    </TabPanel>

                    <TabPanel value={tab} index={1}>
                        <Container maxWidth="xl">
                            {Object.keys(hints).map((site_id) => (
                                <HintViewer
                                    key={site_id}
                                    hints={hints[site_id]}
                                    siteName={getSiteName(site_id)}
                                />
                            ))}
                        </Container>
                    </TabPanel>
                </DialogContent>
            </Dialog>
        </>
    )
}
