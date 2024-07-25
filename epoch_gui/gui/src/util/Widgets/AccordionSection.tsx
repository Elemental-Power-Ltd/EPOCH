import React from 'react';
import { Accordion, AccordionSummary, AccordionDetails, Typography } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

interface AccordionSectionProps {
  title: string;
  children: React.ReactNode;
}

const AccordionSection: React.FC<AccordionSectionProps> = ({ title, children }) => {
  return (
    <Accordion slotProps={{transition: {timeout: 200}}}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls={`${title.toLowerCase().replace(' ', '-')}-content`}
        id={`${title.toLowerCase().replace(' ', '-')}-header`}
      >
        <Typography>{title}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        {children}
      </AccordionDetails>
    </Accordion>
  );
};

export default AccordionSection;
