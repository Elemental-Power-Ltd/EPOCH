import React from "react";
import { Alert, AlertTitle, List, ListItem, ListItemText } from "@mui/material";

interface ErrorListProps {
    errors: string[];
}

const ErrorList: React.FC<ErrorListProps> = ({ errors }) => {
  if (errors.length === 0) return null;

  return (
    <Alert severity="error">
      <AlertTitle>Errors</AlertTitle>
      <List >
        {errors.map((error, index) => (
          <ListItem key={index} disablePadding>
            <ListItemText primary={error} />
          </ListItem>
        ))}
      </List>
    </Alert>
  );
};

export default ErrorList;
