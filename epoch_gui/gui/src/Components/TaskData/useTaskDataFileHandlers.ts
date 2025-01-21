// useTaskDataFileHandlers.ts

import { useState } from "react";

import {ValidationResult, validateTaskData} from "./validateTaskData";

interface UseTaskDataFileHandlersParams {
  setTaskData: (taskData: any) => void;
}

export const useTaskDataFileHandlers = ({
  setTaskData,
}: UseTaskDataFileHandlersParams) => {
  const [error, setError] = useState<string | null>(null);

  const onUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target?.result as string);
        const validation = validateTaskData(json);

        if (validation.valid) {
          setTaskData(json);
        } else {
          alert("Invalid TaskData – see console for details.");
          console.error("Invalid TaskData", validation.result);
        }
      } catch (error) {
        alert("Error parsing JSON file");
      }
    };
    reader.readAsText(file);
  };

  const onDownload = (taskData: any) => {
    let filename = "taskData.json";

    const validation = validateTaskData(taskData);

    if (!validation.valid) {
      alert("Invalid taskData (downloading anyway)");
      filename = "invalidTaskData.json";
    }

    const jsonData = JSON.stringify(taskData, null, 4);
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

  const onCopy = async (taskData: any) => {
    const validation = validateTaskData(taskData);

    if (!validation.valid) {
      alert("Invalid taskData (copying anyway)");
      console.error("Invalid TaskData", validation.result);
    }

    // copy to clipboard either way
    const json = JSON.stringify(taskData, null, 4);
    await navigator.clipboard.writeText(json);
  };

  return {
    onUpload,
    onDownload,
    onCopy,
  };
};
