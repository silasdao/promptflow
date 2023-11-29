# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import logging
import platform

from opencensus.ext.azure.log_exporter import AzureEventHandler

from promptflow._cli._user_agent import USER_AGENT
from promptflow._sdk._configuration import Configuration

# promptflow-sdk in east us
INSTRUMENTATION_KEY = "e46ea0b2-ab2e-4c5e-aa20-95977d802d01"
# promptflow-sdk-eu in west europe
EU_INSTRUMENTATION_KEY = "f2ff886e-8b36-4de3-88da-7ec84fd437e3"


# cspell:ignore overriden
def get_appinsights_log_handler():
    """
    Enable the OpenCensus logging handler for specified logger and instrumentation key to send info to AppInsights.
    """
    from promptflow._sdk._utils import setup_user_agent_to_operation_context
    from promptflow._telemetry.telemetry import is_telemetry_enabled

    try:

        config = Configuration.get_instance()
        if config.is_eu_user():
            instrumentation_key = EU_INSTRUMENTATION_KEY
        else:
            instrumentation_key = INSTRUMENTATION_KEY
        user_agent = setup_user_agent_to_operation_context(USER_AGENT)
        custom_properties = {
            "python_version": platform.python_version(),
            "user_agent": user_agent,
            "installation_id": config.get_or_set_installation_id(),
        }

        return PromptFlowSDKLogHandler(
            connection_string=f"InstrumentationKey={instrumentation_key}",
            custom_properties=custom_properties,
            enable_telemetry=is_telemetry_enabled(),
            eu_user=config.is_eu_user(),
        )
    except Exception:  # pylint: disable=broad-except
        # ignore any exceptions, telemetry collection errors shouldn't block an operation
        return logging.NullHandler()


# cspell:ignore AzureMLSDKLogHandler
class PromptFlowSDKLogHandler(AzureEventHandler):
    """Customized AzureLogHandler for PromptFlow SDK"""

    def __init__(self, custom_properties, enable_telemetry, eu_user, **kwargs):
        super().__init__(**kwargs)

        self._is_telemetry_enabled = enable_telemetry
        self._custom_dimensions = custom_properties
        self.eu_user = eu_user

    def emit(self, record):
        # skip logging if telemetry is disabled
        if not self._is_telemetry_enabled:
            return

        try:
            self._queue.put(record, block=False)

            # log the record immediately if it is an error
            if record.exc_info and any(
                item is not None for item in record.exc_info
            ):
                self._queue.flush()
        except Exception:  # pylint: disable=broad-except
            # ignore any exceptions, telemetry collection errors shouldn't block an operation
            return

    def log_record_to_envelope(self, record):
        from promptflow._utils.utils import is_in_ci_pipeline

        # skip logging if telemetry is disabled

        if not self._is_telemetry_enabled:
            return
        custom_dimensions = {
            "level": record.levelname,
            # add to distinguish if the log is from ci pipeline
            "from_ci": is_in_ci_pipeline(),
        }
        custom_dimensions.update(self._custom_dimensions)
        if hasattr(record, "custom_dimensions") and isinstance(record.custom_dimensions, dict):
            record.custom_dimensions.update(custom_dimensions)
        else:
            record.custom_dimensions = custom_dimensions

        return super().log_record_to_envelope(record=record)
