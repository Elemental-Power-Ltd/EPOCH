import * as React from "react";
import {Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Divider, Stack, Typography} from "@mui/material";


type AboutProps = {
    open: boolean;
    onClose: () => void;
}

const AboutDemo: React.FC<AboutProps> = ({open, onClose}) => {
    const howItWorks = () => {
        const steps: Array<React.ReactNode> = [
            "Pick a site.",
            "Choose the upgrades you want to install.",
            <>Click <strong>Simulate</strong> to run a year-long energy simulation.</>,
        ];

        const stepColors = ["primary", "primary", "success"] as const;

        return (
            <Stack spacing={1.25}>
                <Typography variant="body2">
                    Find the most cost-efficient ways to decarbonise:
                </Typography>
                {steps.map((text, i) => (
                    <Box key={i} sx={{display: "flex", alignItems: "flex-start", gap: 1.25}}>
                        <Chip
                            label={i + 1}
                            size="small"
                            color={stepColors[i]}
                            sx={{
                                minWidth: 20,
                                height: 20,
                                borderRadius: "999px",
                                fontWeight: 700,
                                mt: "2px",
                            }}
                        />
                        <Typography variant="body1">{text}</Typography>
                    </Box>
                ))}
            </Stack>
        );
    };

    const devs = [
        {name: "Jon Warren", link: "https://github.com/JonWarrenDev"},
        {name: "Matt Bailey", link: "https://github.com/Matt-HJ-Bailey"},
        {name: "Will Drouard", link: "https://github.com/WilliamGTD"},
        {name: "Andy Scott", link: "https://github.com/AndyEPL"},
        {name: "James Martin", link: "https://github.com/jsmartinstats"},
        {name: "Simon Le Blond", link: "https://github.com/Simon-EPL"}
    ]

    // randomly order the devs, don't want to show favouritism!
    const shuffledDevs = [...devs].sort(() => Math.random() - 0.5);

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>EPOCH Demonstrator</DialogTitle>

            <DialogContent dividers>
                {howItWorks()}

                <Divider sx={{ my: 2 }} />

                <Typography variant="body1" sx={{fontWeight: 600, mt: 2}} gutterBottom>
                    About EPOCH
                </Typography>

                <Typography variant="body2" color="text.secondary" paragraph>
                    This demonstrator uses pre-prepared data to provide a simplified version of <strong>EPOCH</strong>, our energy optimisation service.
                     The full set of tools can also:
                </Typography>

                <Typography
                    component="ul"
                    sx={{mt: 0, mb: 2, pl: 3, "& li": {mb: 0.75}}}
                >
                    <li><Typography component="span" variant="body2">Generate data for any location</Typography></li>
                    <li><Typography component="span" variant="body2">Synthesise half-hourly demand profiles from coarse
                        or
                        incomplete meter readings</Typography></li>
                    <li><Typography component="span" variant="body2">Search large numbers of permutations to identify the best
                        interventions</Typography></li>
                    <li><Typography component="span" variant="body2">Optimise across a portfolio with a shared
                        budget</Typography></li>
                    <li><Typography component="span" variant="body2">Trade off different objectives and
                        constraints</Typography></li>
                    <li><Typography component="span" variant="body2">Model a wider range of components and
                        behaviours</Typography></li>
                </Typography>

                <Divider sx={{ my: 2 }} />

                <Typography variant="body2" color="text.secondary">
                  EPOCH was developed at Elemental Power Ltd by:{" "}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {shuffledDevs.map((dev, index) => (
                    <span key={dev.link}>
                      <Button
                        component="a"
                        href={dev.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        variant="text"
                        size="small"
                        sx={{
                          textTransform: "none",
                          px: 0,
                          minWidth: "auto",
                          verticalAlign: "baseline",
                        }}
                      >
                        {dev.name}
                      </Button>

                      {index < shuffledDevs.length - 2 && ", "}
                      {index === shuffledDevs.length - 2 && " and "}
                    </span>
                  ))}
                  .
                </Typography>

                <Typography variant="body2" color="text.secondary">
                    See the project on{" "}
                    <Button
                        component="a"
                        href="https://github.com/elemental-Power-Ltd/EPOCH"
                        target="_blank"
                        rel="noopener noreferrer"
                        variant="text"
                        size="small"
                        sx={{textTransform: "none", px: 0, minWidth: "auto", verticalAlign: "baseline"}}
                    >
                        GitHub
                    </Button>
                    .
                </Typography>
            </DialogContent>

            <DialogActions>
                <Button onClick={onClose} autoFocus>
                    Close
                </Button>
            </DialogActions>
        </Dialog>
    );
}

export default AboutDemo;