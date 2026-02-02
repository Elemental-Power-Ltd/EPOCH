from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from epoch_simulator import ReportData


def report_data_to_dict(report_data: ReportData) -> dict[str, list[float]]:
    """
    Convert the ReportData type returned as part of a SimulationResult into a more generic dict type.

    This is a convenience method to make the type we provide to the GUI generic (for now).

    Parameters
    ----------
    report_data
        The python bindings for the EPOCH ReportData struct

    Returns
    -------
        A dictionary representation of the report_data
    """

    def filter_report_data_fields(fields: list[str]) -> list[str]:
        """
        Crude method of finding the useful report data's fields.

        Filter out the methods that start with "__" and "_pybind11_conduit_v1_".

        Parameters
        ----------
        fields
            list of fields to filter.

        Returns
        -------
            list of filtered fields.
        """
        return [field for field in fields if field != "_pybind11_conduit_v1_" and not field.startswith("__")]

    report_dict = {}
    if report_data is not None:
        fields = filter_report_data_fields(fields=dir(report_data))

        # all fields are currently numpy arrays
        # we want the non-zero arrays
        for field in fields:
            vector = getattr(report_data, field)
            if vector.any():
                report_dict[field] = vector.tolist()
    return report_dict
