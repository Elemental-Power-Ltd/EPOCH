import React, {useMemo, useState } from 'react';
import {
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  TablePagination,
  Menu,
  MenuItem,
  Checkbox
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ViewColumnIcon from '@mui/icons-material/ViewColumn';

import { OptimisationTaskListEntry } from "../../State/types";
import { parseISODuration } from "../../util/displayFunctions";
import {metricDefs} from "../../util/MetricDefinitions.ts";

interface TaskTableProps {
  tasks: OptimisationTaskListEntry[];
  total: number;
  page: number;
  rowsPerPage: number;
  onPageChange: (page: number) => void;
  onRowsPerPageChange: (rows: number) => void;

  selectTask: (task_id: string) => void;
  deselectTask: () => void;
  selectedTaskId?: string;
}
type ColumnKey =
  | 'task_name'
  | 'n_evals'
  | 'exec_time'
  | 'created_at'
  | 'epoch_version'
  | 'objectives'
  | 'n_saved'
  | 'actions';

const ALL_COLUMNS: { key: ColumnKey; label: string; required?: boolean }[] = [
  { key: 'task_name', label: 'Task Name', required: true },
  { key: 'n_evals', label: 'Number of Evaluations' },
  { key: 'exec_time', label: 'Exec Time' },
  { key: 'created_at', label: 'Created' },
  { key: 'epoch_version', label: 'Epoch Version' },
  { key: 'objectives', label: 'Objectives' },
  { key: 'n_saved', label: 'Number of Results' },
  { key: 'actions', label: '', required: true } // selectTask column (mandatory)
];

const OPTIONAL_COLUMN_KEYS = ALL_COLUMNS.filter(c => !c.required).map(c => c.key) as ColumnKey[];
const HIDE_BY_DEFAULT: ColumnKey[] = ['n_evals', 'exec_time', 'epoch_version'];

const TaskTable: React.FC<TaskTableProps> = ({ tasks, total, page, rowsPerPage, onPageChange, onRowsPerPageChange, selectTask, deselectTask, selectedTaskId }) => {

  // if a task has been selected, we only show the user that task
  // (as they will be more interested in viewing the portfolio results table)
  // if they have not selected a task, show all task results
  const tasksToShow = tasks.filter(
      (task) => (!selectedTaskId || task.task_id === selectedTaskId)
  );


  const formatDateTime = (iso: string | null) => {
    if (!iso) return "-";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const displayObjectives = (objectives: string[]): string => {
    return objectives.map(obj => metricDefs[obj as keyof typeof metricDefs].label).join(' • ');
  }

  // ---- Column visibility control ----
  const [visibleOptional, setVisibleOptional] = useState<Set<ColumnKey>>(
    () => new Set<ColumnKey>(OPTIONAL_COLUMN_KEYS.filter(k => !HIDE_BY_DEFAULT.includes(k)))
  );
  const [columnsAnchorEl, setColumnsAnchorEl] = useState<null | HTMLElement>(null);
  const columnsMenuOpen = Boolean(columnsAnchorEl);
  const handleOpenColumns = (e: React.MouseEvent<HTMLButtonElement>) => setColumnsAnchorEl(e.currentTarget);
  const handleCloseColumns = () => setColumnsAnchorEl(null);

  const toggleColumn = (key: ColumnKey) => {
    if (!OPTIONAL_COLUMN_KEYS.includes(key)) return; // ignore mandatory
    setVisibleOptional(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const visibleColumns = useMemo(
    () => ALL_COLUMNS.filter(c => c.required || visibleOptional.has(c.key)),
    [visibleOptional]
  );

  return (
    <>
      <Box marginBottom={2} display="flex" justifyContent="space-between" alignItems="center">
        <Box>
          {selectedTaskId && (
            <Button startIcon={<ArrowBackIcon />} onClick={deselectTask}>
              Show all Tasks
            </Button>
          )}
        </Box>

        <Box>
          <Button
            variant="outlined"
            startIcon={<ViewColumnIcon />}
            onClick={handleOpenColumns}
            aria-haspopup="true"
            aria-controls={columnsMenuOpen ? 'columns-menu' : undefined}
          >
            Columns
          </Button>

          <Menu
            id="columns-menu"
            anchorEl={columnsAnchorEl}
            open={columnsMenuOpen}
            onClose={handleCloseColumns}
          >
            {OPTIONAL_COLUMN_KEYS.map(key => {
              const col = ALL_COLUMNS.find(c => c.key === key)!;
              const checked = visibleOptional.has(key);
              return (
                <MenuItem
                  key={key}
                  dense
                  role="menuitemcheckbox"
                  aria-checked={checked}
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleColumn(key);
                  }}
                >
                  {/* No onChange here to avoid double toggles; clicking the box will bubble to MenuItem and toggle once */}
                  <Checkbox
                    checked={checked}
                    tabIndex={-1}
                    disableRipple
                  />
                  {col.label}
                </MenuItem>
              );
            })}
          </Menu>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              {visibleColumns.map(col => (
                <TableCell key={col.key}>{col.label}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {tasksToShow.map(task => (
              <TableRow key={task.task_id}>
                {visibleColumns.map(col => {
                  switch (col.key) {
                    case 'task_name':
                      return <TableCell key={col.key}>{task.task_name || 'Unnamed Task'}</TableCell>;
                    case 'n_evals':
                      return <TableCell key={col.key}>{task.n_evals || "-"}</TableCell>;
                    case 'exec_time':
                      return <TableCell key={col.key}>{parseISODuration(task.exec_time)}</TableCell>;
                    case 'created_at':
                      return <TableCell key={col.key}>{formatDateTime(task.created_at)}</TableCell>;
                    case 'epoch_version':
                      return <TableCell key={col.key}>{task.epoch_version || "-"}</TableCell>;
                    case 'objectives':
                      return (
                        <TableCell key={col.key} sx={{ maxWidth: 280 }}>
                          {task.objectives && task.objectives.length ? (
                            <Box
                              sx={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
                              title={task.objectives.join(', ')}
                            >
                              {displayObjectives(task.objectives)}
                            </Box>
                          ) : "—"}
                        </TableCell>
                      );
                    case 'n_saved':
                      return <TableCell key={col.key}>{task.n_saved ? task.n_saved : 0}</TableCell>;
                    case 'actions':
                      return (
                        <TableCell key={col.key}>
                          <IconButton color="primary" onClick={() => selectTask(task.task_id)}>
                            <ArrowForwardIcon />
                          </IconButton>
                        </TableCell>
                      );
                    default:
                      return null;
                  }
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {/* we hide pagination when a specific task is selected */}
        {!selectedTaskId && (
          <TablePagination
            component="div"
            count={total}
            page={page}
            onPageChange={(_, newPage) => onPageChange(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => onRowsPerPageChange(parseInt(e.target.value, 10))}
            rowsPerPageOptions={[10, 20, 50, 100]}
          />
        )}
      </TableContainer>
    </>
  );
};

export default TaskTable;
