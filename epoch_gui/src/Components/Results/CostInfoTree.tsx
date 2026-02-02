import * as React from "react";
import {
    Box,
    Chip,
    Collapse,
    Divider,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Stack,
    Typography,
} from "@mui/material";
import FolderIcon from "@mui/icons-material/Folder";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";
import CurrencyPoundIcon from "@mui/icons-material/CurrencyPound";

import type {CostInfo} from "../../State/types.ts";

type CostInfoTreeProps = {
    /** Top-level items to display */
    items: CostInfo[];
    /** ISO 4217 currency code; defaults to GBP */
    currency?: string;
    /** Whether all nodes start expanded */
    initialExpanded?: boolean;
    /** Optional: render a header title above the list */
    title?: React.ReactNode;
    /** Provided externally; not computed from the tree */
    totalCapex?: number;
};

const currencyFormatter = (currency = "GBP") =>
    new Intl.NumberFormat(undefined, {
        style: "currency",
        currency,
        maximumFractionDigits: 0,
    });

export const CostInfoTree: React.FC<CostInfoTreeProps> = ({
                                                              items,
                                                              currency = "GBP",
                                                              initialExpanded = false,
                                                              title,
                                                              totalCapex,
                                                          }) => {
    const fmt = React.useMemo(() => currencyFormatter(currency), [currency]);

    return (
        <Box>
            <List disablePadding>
                {items.map((item, idx) => (
                    <React.Fragment key={`${item.name}-${idx}`}>
                        <CostItem
                            item={item}
                            fmt={fmt}
                            depth={0}
                            initialExpanded={initialExpanded}
                        />
                        {idx < items.length - 1 && <Divider component="li"/>}
                    </React.Fragment>
                ))}
            </List>
            {(title || typeof totalCapex === "number") && (
                <Stack
                    direction="row"
                    alignItems="center"
                    justifyContent="space-between"
                    sx={{mb: 1}}
                >
                    {title ? (
                        <Typography variant="h6">{title}</Typography>
                    ) : (
                        <span/>
                    )}
                    {typeof totalCapex === "number" && (
                        <Chip
                            icon={<CurrencyPoundIcon/>}
                            label={`Total CAPEX ${fmt.format(totalCapex)}`}
                            variant="outlined"
                        />
                    )}
                </Stack>
            )}

        </Box>
    );
};

type CostItemProps = {
    item: CostInfo;
    fmt: Intl.NumberFormat;
    depth: number;
    initialExpanded: boolean;
};

const CostItem: React.FC<CostItemProps> = ({
                                               item,
                                               fmt,
                                               depth,
                                               initialExpanded,
                                           }) => {
    const hasChildren =
        Array.isArray(item.sub_components) && item.sub_components.length > 0;
    const [open, setOpen] = React.useState<boolean>(
        initialExpanded && hasChildren
    );

    const handleToggle = () => {
        if (hasChildren) setOpen((v) => !v);
    };

    return (
        <>
            <ListItem
                disableGutters
                sx={{
                    pl: (theme) => theme.spacing(1 + depth * 2),
                    pr: 1,
                }}
                secondaryAction={
                    <Stack direction="row" alignItems="center" spacing={0.5}>
                        <CurrencyPoundIcon fontSize="small"/>
                        <Typography
                            variant="body2"
                            sx={{minWidth: 80, textAlign: "right"}}
                        >
                            {fmt.format(item.cost)}
                        </Typography>
                    </Stack>
                }
            >
                <ListItemButton
                    onClick={handleToggle}
                    disableRipple={!hasChildren}
                    sx={{borderRadius: 1}}
                    aria-expanded={hasChildren ? open : undefined}
                    aria-label={hasChildren ? `Toggle ${item.name} sub-items` : undefined}
                >
                    <ListItemIcon sx={{minWidth: 32}}>
                        {hasChildren ? <FolderIcon/> : <InsertDriveFileIcon/>}
                    </ListItemIcon>

                    <ListItemText
                        primary={
                            <Typography variant="body1" fontWeight={500}>
                                {item.name}
                            </Typography>
                        }
                        secondary={
                            hasChildren ? (
                                <Stack
                                    direction="row"
                                    spacing={0.5}
                                    alignItems="center"
                                    component="span"
                                >
                                    <Typography
                                        variant="caption"
                                        color="text.secondary"
                                        component="span"
                                    >
                                        {item.sub_components.length} sub-component
                                        {item.sub_components.length === 1 ? "" : "s"}
                                    </Typography>
                                    {open ? (
                                        <ExpandLess fontSize="small"/>
                                    ) : (
                                        <ExpandMore fontSize="small"/>
                                    )}
                                </Stack>
                            ) : undefined
                        }
                    />
                </ListItemButton>
            </ListItem>

            {hasChildren && (
                <Collapse in={open} timeout="auto" unmountOnExit>
                    <List disablePadding>
                        {item.sub_components.map((child, idx) => (
                            <CostItem
                                key={`${child.name}-${depth + 1}-${idx}`}
                                item={child}
                                fmt={fmt}
                                depth={depth + 1}
                                initialExpanded={initialExpanded}
                            />
                        ))}
                    </List>
                </Collapse>
            )}
        </>
    );
};
