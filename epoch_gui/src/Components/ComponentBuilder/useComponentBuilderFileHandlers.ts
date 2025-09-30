
import {validateTaskData, validateSiteRange} from "./ValidateBuilders";
import {BuilderMode} from "../../Models/Core/ComponentBuilder";

interface UseFileHandlerProps {
  mode: BuilderMode;
  setData: (data: any) => void;
}

export const useComponentBuilderFileHandlers = ({mode, setData}: UseFileHandlerProps) => {

  const CamelCaseName = (mode === "TaskDataMode") ? "TaskData" : "SiteRange";
  const validate = (mode === "TaskDataMode") ? validateTaskData : validateSiteRange;

  /**
   * Remove any top-level null fields from a JSON object
   * This is used as a helper to provide a clean version of TaskData / SiteRange when uploading & downloading
   */
  const removeTopLevelNulls = (json: any): any => {
    if (json === null || typeof json !== 'object' || Array.isArray(json)) {
      return json;
    }

    const result: Record<string, any> = {};

    for (const [key, value] of Object.entries(json)) {
      if (value !== null) {
        result[key] = value;
      }
    }

    return result;
  };


  const onUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const jsonWithNulls = JSON.parse(e.target?.result as string);
        const json = removeTopLevelNulls(jsonWithNulls);
        const validation = validate(json);

        if (validation.valid) {
          setData(json);
        } else {
          alert(`Invalid ${CamelCaseName} – see console for details.`);
          console.error(`Invalid ${CamelCaseName}`, validation.result);
        }
      } catch (error) {
        alert("Error parsing JSON file");
      }
    };
    reader.readAsText(file);
  };

  const onDownload = (data: any, nameHint?: string) => {

    let filename = nameHint ? `${nameHint}_${CamelCaseName}.json` : `${CamelCaseName}.json`;

    const validation = validate(data);

    if (!validation.valid) {
      alert(`Invalid ${CamelCaseName} (downloading anyway)`);
      filename = "invalid" + filename;
    }

    const jsonData = JSON.stringify(data, null, 4);
    const blob = new Blob([jsonData], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // FIXME - navigator.clipboard isn't available in insecure contexts (http)
  const onCopy = async (data: any) => {
    const validation = validate(data);

    if (!validation.valid) {
      alert(`Invalid ${CamelCaseName} (copying anyway)`);
      console.error(`Invalid ${CamelCaseName}, copying anyway`, validation.result);
    }

    // copy to clipboard either way
    const json = JSON.stringify(data, null, 4);
    await navigator.clipboard.writeText(json);
  };

  return {
    onUpload,
    onDownload,
    onCopy,
  };
};
