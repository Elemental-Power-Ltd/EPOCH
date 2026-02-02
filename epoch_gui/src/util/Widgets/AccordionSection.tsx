import React, {useState} from 'react';
import {Accordion, AccordionSummary, AccordionDetails, Typography} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

interface AccordionSectionProps {
    title: string;
    children: React.ReactNode;
    error: boolean;
}

const AccordionSection: React.FC<AccordionSectionProps> = ({title, children, error}) => {
  const [expanded, setExpanded] = useState(false);

    return (
        <Accordion
            slotProps={{transition: {timeout: 200}}}
            onChange={(_, isExpanded) => setExpanded(isExpanded)}
        >
            <AccordionSummary
                expandIcon={<ExpandMoreIcon/>}
                aria-controls={`${title.toLowerCase().replace(' ', '-')}-content`}
                id={`${title.toLowerCase().replace(' ', '-')}-header`}
            >
                <Typography color={error ? 'error' : 'inherit'}>
                    {error && <ErrorOutlineIcon fontSize="small" sx={{marginRight: 1}}/>}
                    {title}
                </Typography>
            </AccordionSummary>
            {expanded &&
                <AccordionDetails>
                {children}
                </AccordionDetails>
            }
        </Accordion>
    );
};

export default AccordionSection;
