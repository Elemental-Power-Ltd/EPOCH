import {FC, useState} from "react";
import {Button, Alert} from "@mui/material";
import SiteDataForm from "../TaskConfig/SiteDataForm";
import {ApiResponse, getSiteBaseline} from "../../endpoints";
import dayjs, {Dayjs} from "dayjs";
import {TaskData} from "../TaskDataViewer/TaskData.ts";
import {Site} from "../../State/types.ts";

interface Props {
  clientSites: Site[];
  onBaselineReady: (
    baseline: TaskData,
    siteID: string,
    startDate: Dayjs,
    timestep: number
  ) => void;
}

const SiteSelector: FC<Props> = ({clientSites, onBaselineReady}) => {
  // when there's only 1 site, pre-populate this form
  const [siteID, setSiteID] = useState(clientSites.length === 1 ? clientSites[0].site_id : "");
  const [startDate, setStartDate] = useState<Dayjs | null>(
    dayjs("2022-01-01T00:00:00Z")
  );
  const [timestep, setTimestep] = useState(30);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canProgress = (): boolean => {
    const isSiteIdValid = clientSites.some(s => s.site_id === siteID);
    const isStartDateValid = Boolean(startDate);
    const isDurationValid = Boolean(timestep);
    return isSiteIdValid && isStartDateValid && isDurationValid;
  };

  const handleNext = async () => {
    if (!canProgress()) {
      setError("Please complete all required site fields.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const response: ApiResponse<TaskData> = await getSiteBaseline(siteID);
      if (response.success && response.data) {
        onBaselineReady(response.data, siteID, startDate!, timestep);
      } else {
        setError(response.error ?? "Failed to fetch baseline.");
      }
    } catch {
      setError("Network error while fetching baseline.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <SiteDataForm
        siteId={siteID}
        onSiteChange={setSiteID}
        startDate={startDate}
        onStartDateChange={setStartDate}
        timestepMinutes={timestep}
        onTimestepChange={setTimestep}
        clientSites={clientSites}
      />

      {error && <Alert severity="error" sx={{mt: 2}}>{error}</Alert>}

      <Button
        variant="contained"
        color="primary"
        onClick={handleNext}
        disabled={loading}
        sx={{mt: 3}}
      >
        Next
      </Button>
    </>
  );
};

export default SiteSelector;
