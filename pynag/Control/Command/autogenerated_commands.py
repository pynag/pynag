

def add_host_comment(
    host_name,
    persistent,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Adds a comment to a particular host.  If the "persistent" field
    is set to zero (0), the comment will be deleted the next time
    Nagios is restarted.  Otherwise, the comment will persist across
    program restarts until it is deleted manually.
    """
    return send_command("ADD_HOST_COMMENT",
                        command_file,
                        timestamp,
                        host_name,
                        persistent,
                        author,
                        comment)


def shutdown_program(
    command_file=None,
    timestamp=0
):
    """
    Shuts down the Nagios process.
    """
    return send_command("SHUTDOWN_PROGRAM",
                        command_file,
                        timestamp,
                        )


def disable_servicegroup_passive_svc_checks(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables the acceptance and processing of passive checks for all
    services in a particular servicegroup.
    """
    return send_command("DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS",
                        command_file,
                        timestamp,
                        servicegroup_name)


def enable_servicegroup_passive_host_checks(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables the acceptance and processing of passive checks for all
    hosts that have services that are members of a particular
    service group.
    """
    return send_command("ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS",
                        command_file,
                        timestamp,
                        servicegroup_name)


def disable_servicegroup_passive_host_checks(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables the acceptance and processing of passive checks for all
    hosts that have services that are members of a particular
    service group.
    """
    return send_command("DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS",
                        command_file,
                        timestamp,
                        servicegroup_name)


def change_global_host_event_handler(
    event_handler_command,
    command_file=None,
    timestamp=0
):
    """
    Changes the global host event handler command to be that
    specified by the "event_handler_command" option.  The
    "event_handler_command" option specifies the short name of the
    command that should be used as the new host event handler.  The
    command must have been configured in Nagios before it was last
    (re)started.
    """
    return send_command("CHANGE_GLOBAL_HOST_EVENT_HANDLER",
                        command_file,
                        timestamp,
                        event_handler_command)


def change_global_svc_event_handler(
    event_handler_command,
    command_file=None,
    timestamp=0
):
    """
    Changes the global service event handler command to be that
    specified by the "event_handler_command" option.  The
    "event_handler_command" option specifies the short name of the
    command that should be used as the new service event handler.
    The command must have been configured in Nagios before it was
    last (re)started.
    """
    return send_command("CHANGE_GLOBAL_SVC_EVENT_HANDLER",
                        command_file,
                        timestamp,
                        event_handler_command)


def change_host_event_handler(
    host_name,
    event_handler_command,
    command_file=None,
    timestamp=0
):
    """
    Changes the event handler command for a particular host to be
    that specified by the "event_handler_command" option.  The
    "event_handler_command" option specifies the short name of the
    command that should be used as the new host event handler.  The
    command must have been configured in Nagios before it was last
    (re)started.
    """
    return send_command("CHANGE_HOST_EVENT_HANDLER",
                        command_file,
                        timestamp,
                        host_name,
                        event_handler_command)


def change_svc_event_handler(
    host_name,
    service_description,
    event_handler_command,
    command_file=None,
    timestamp=0
):
    """
    Changes the event handler command for a particular service to be
    that specified by the "event_handler_command" option.  The
    "event_handler_command" option specifies the short name of the
    command that should be used as the new service event handler.
    The command must have been configured in Nagios before it was
    last (re)started.
    """
    return send_command("CHANGE_SVC_EVENT_HANDLER",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        event_handler_command)


def change_host_check_command(
    host_name,
    check_command,
    command_file=None,
    timestamp=0
):
    """
    Changes the check command for a particular host to be that
    specified by the "check_command" option.  The "check_command"
    option specifies the short name of the command that should be
    used as the new host check command.  The command must have been
    configured in Nagios before it was last (re)started.
    """
    return send_command("CHANGE_HOST_CHECK_COMMAND",
                        command_file,
                        timestamp,
                        host_name,
                        check_command)


def change_svc_check_command(
    host_name,
    service_description,
    check_command,
    command_file=None,
    timestamp=0
):
    """
    Changes the check command for a particular service to be that
    specified by the "check_command" option.  The "check_command"
    option specifies the short name of the command that should be
    used as the new service check command.  The command must have
    been configured in Nagios before it was last (re)started.
    """
    return send_command("CHANGE_SVC_CHECK_COMMAND",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        check_command)


def change_normal_host_check_interval(
    host_name,
    check_interval,
    command_file=None,
    timestamp=0
):
    """
    Changes the normal (regularly scheduled) check interval for a
    particular host.
    """
    return send_command("CHANGE_NORMAL_HOST_CHECK_INTERVAL",
                        command_file,
                        timestamp,
                        host_name,
                        check_interval)


def enable_svc_notifications(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Enables notifications for a particular service.  Notifications
    will be sent out for the service only if notifications are
    enabled on a program-wide basis as well.
    """
    return send_command("ENABLE_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def change_normal_svc_check_interval(
    host_name,
    service_description,
    check_interval,
    command_file=None,
    timestamp=0
):
    """
    Changes the normal (regularly scheduled) check interval for a
    particular service
    """
    return send_command("CHANGE_NORMAL_SVC_CHECK_INTERVAL",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        check_interval)


def change_retry_svc_check_interval(
    host_name,
    service_description,
    check_interval,
    command_file=None,
    timestamp=0
):
    """
    Changes the retry check interval for a particular service.
    """
    return send_command("CHANGE_RETRY_SVC_CHECK_INTERVAL",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        check_interval)


def change_max_host_check_attempts(
    host_name,
    check_attempts,
    command_file=None,
    timestamp=0
):
    """
    Changes the maximum number of check attempts (retries) for a
    particular host.
    """
    return send_command("CHANGE_MAX_HOST_CHECK_ATTEMPTS",
                        command_file,
                        timestamp,
                        host_name,
                        check_attempts)


def change_max_svc_check_attempts(
    host_name,
    service_description,
    check_attempts,
    command_file=None,
    timestamp=0
):
    """
    Changes the maximum number of check attempts (retries) for a
    particular service.
    """
    return send_command("CHANGE_MAX_SVC_CHECK_ATTEMPTS",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        check_attempts)


def process_service_check_result(
    host_name,
    service_description,
    return_code,
    plugin_output,
    command_file=None,
    timestamp=0
):
    """
    This is used to submit a passive check result for a particular
    service.  The "return_code" field should be one of the
    following: 0=OK, 1=WARNING, 2=CRITICAL, 3=UNKNOWN.  The
    "plugin_output" field contains text output from the service
    check, along with optional performance data.
    """
    return send_command("PROCESS_SERVICE_CHECK_RESULT",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        return_code,
                        plugin_output)


def process_host_check_result(
    host_name,
    status_code,
    plugin_output,
    command_file=None,
    timestamp=0
):
    """
    This is used to submit a passive check result for a particular
    host.  The "status_code" indicates the state of the host check
    and should be one of the following: 0=UP, 1=DOWN, 2=UNREACHABLE.
    The "plugin_output" argument contains the text returned from the
    host check, along with optional performance data.
    """
    return send_command("PROCESS_HOST_CHECK_RESULT",
                        command_file,
                        timestamp,
                        host_name,
                        status_code,
                        plugin_output)


def remove_host_acknowledgement(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    This removes the problem acknowledgement for a particular host.
    Once the acknowledgement has been removed, notifications can
    once again be sent out for the given host.
    """
    return send_command("REMOVE_HOST_ACKNOWLEDGEMENT",
                        command_file,
                        timestamp,
                        host_name)


def remove_svc_acknowledgement(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    This removes the problem acknowledgement for a particular
    service.  Once the acknowledgement has been removed,
    notifications can once again be sent out for the given service.
    """
    return send_command("REMOVE_SVC_ACKNOWLEDGEMENT",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def schedule_host_downtime(
    host_name,
    start_time,
    end_time,
    fixed,
    trigger_id,
    duration,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Schedules downtime for a specified host.  If the "fixed"
    argument is set to one (1), downtime will start and end at the
    times specified by the "start" and "end" arguments.  Otherwise,
    downtime will begin between the "start" and "end" times and last
    for "duration" seconds.  The "start" and "end" arguments are
    specified in time_t format (seconds since the UNIX epoch).  The
    specified host downtime can be triggered by another downtime
    entry if the "trigger_id" is set to the ID of another scheduled
    downtime entry.  Set the "trigger_id" argument to zero (0) if
    the downtime for the specified host should not be triggered by
    another downtime entry.
    """
    return send_command("SCHEDULE_HOST_DOWNTIME",
                        command_file,
                        timestamp,
                        host_name,
                        start_time,
                        end_time,
                        fixed,
                        trigger_id,
                        duration,
                        author,
                        comment)


def schedule_svc_downtime(
    host_name,
    service_description,
    start_time,
    end_time,
    fixed,
    trigger_id,
    duration,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Schedules downtime for a specified service.  If the "fixed"
    argument is set to one (1), downtime will start and end at the
    times specified by the "start" and "end" arguments.  Otherwise,
    downtime will begin between the "start" and "end" times and last
    for "duration" seconds.  The "start" and "end" arguments are
    specified in time_t format (seconds since the UNIX epoch).  The
    specified service downtime can be triggered by another downtime
    entry if the "trigger_id" is set to the ID of another scheduled
    downtime entry.  Set the "trigger_id" argument to zero (0) if
    the downtime for the specified service should not be triggered
    by another downtime entry.
    """
    return send_command("SCHEDULE_SVC_DOWNTIME",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        start_time,
                        end_time,
                        fixed,
                        trigger_id,
                        duration,
                        author,
                        comment)


def disable_svc_notifications(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Disables notifications for a particular service.
    """
    return send_command("DISABLE_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def schedule_servicegroup_svc_downtime(
    servicegroup_name,
    start_time,
    end_time,
    fixed,
    trigger_id,
    duration,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Schedules downtime for all services in a specified servicegroup.
    If the "fixed" argument is set to one (1), downtime will start
    and end at the times specified by the "start" and "end"
    arguments.  Otherwise, downtime will begin between the "start"
    and "end" times and last for "duration" seconds.  The "start"
    and "end" arguments are specified in time_t format (seconds
    since the UNIX epoch).  The service downtime entries can be
    triggered by another downtime entry if the "trigger_id" is set
    to the ID of another scheduled downtime entry.  Set the
    "trigger_id" argument to zero (0) if the downtime for the
    services should not be triggered by another downtime entry.
    """
    return send_command("SCHEDULE_SERVICEGROUP_SVC_DOWNTIME",
                        command_file,
                        timestamp,
                        servicegroup_name,
                        start_time,
                        end_time,
                        fixed,
                        trigger_id,
                        duration,
                        author,
                        comment)


def schedule_servicegroup_host_downtime(
    servicegroup_name,
    start_time,
    end_time,
    fixed,
    trigger_id,
    duration,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Schedules downtime for all hosts that have services in a
    specified servicegroup.  If the "fixed" argument is set to one
    (1), downtime will start and end at the times specified by the
    "start" and "end" arguments.  Otherwise, downtime will begin
    between the "start" and "end" times and last for "duration"
    seconds.  The "start" and "end" arguments are specified in
    time_t format (seconds since the UNIX epoch).  The host downtime
    entries can be triggered by another downtime entry if the
    "trigger_id" is set to the ID of another scheduled downtime
    entry.  Set the "trigger_id" argument to zero (0) if the
    downtime for the hosts should not be triggered by another
    downtime entry.
    """
    return send_command("SCHEDULE_SERVICEGROUP_HOST_DOWNTIME",
                        command_file,
                        timestamp,
                        servicegroup_name,
                        start_time,
                        end_time,
                        fixed,
                        trigger_id,
                        duration,
                        author,
                        comment)


def schedule_host_svc_downtime(
    host_name,
    start_time,
    end_time,
    fixed,
    trigger_id,
    duration,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Schedules downtime for all services associated with a particular
    host.  If the "fixed" argument is set to one (1), downtime will
    start and end at the times specified by the "start" and "end"
    arguments.  Otherwise, downtime will begin between the "start"
    and "end" times and last for "duration" seconds.  The "start"
    and "end" arguments are specified in time_t format (seconds
    since the UNIX epoch).  The service downtime entries can be
    triggered by another downtime entry if the "trigger_id" is set
    to the ID of another scheduled downtime entry.  Set the
    "trigger_id" argument to zero (0) if the downtime for the
    services should not be triggered by another downtime entry.
    """
    return send_command("SCHEDULE_HOST_SVC_DOWNTIME",
                        command_file,
                        timestamp,
                        host_name,
                        start_time,
                        end_time,
                        fixed,
                        trigger_id,
                        duration,
                        author,
                        comment)


def schedule_hostgroup_host_downtime(
    hostgroup_name,
    start_time,
    end_time,
    fixed,
    trigger_id,
    duration,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Schedules downtime for all hosts in a specified hostgroup.  If
    the "fixed" argument is set to one (1), downtime will start and
    end at the times specified by the "start" and "end" arguments.
    Otherwise, downtime will begin between the "start" and "end"
    times and last for "duration" seconds.  The "start" and "end"
    arguments are specified in time_t format (seconds since the UNIX
    epoch).  The host downtime entries can be triggered by another
    downtime entry if the "trigger_id" is set to the ID of another
    scheduled downtime entry.  Set the "trigger_id" argument to zero
    (0) if the downtime for the hosts should not be triggered by
    another downtime entry.
    """
    return send_command("SCHEDULE_HOSTGROUP_HOST_DOWNTIME",
                        command_file,
                        timestamp,
                        hostgroup_name,
                        start_time,
                        end_time,
                        fixed,
                        trigger_id,
                        duration,
                        author,
                        comment)


def schedule_hostgroup_svc_downtime(
    hostgroup_name,
    start_time,
    end_time,
    fixed,
    trigger_id,
    duration,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Schedules downtime for all services associated with hosts in a
    specified servicegroup.  If the "fixed" argument is set to one
    (1), downtime will start and end at the times specified by the
    "start" and "end" arguments.  Otherwise, downtime will begin
    between the "start" and "end" times and last for "duration"
    seconds.  The "start" and "end" arguments are specified in
    time_t format (seconds since the UNIX epoch).  The service
    downtime entries can be triggered by another downtime entry if
    the "trigger_id" is set to the ID of another scheduled downtime
    entry.  Set the "trigger_id" argument to zero (0) if the
    downtime for the services should not be triggered by another
    downtime entry.
    """
    return send_command("SCHEDULE_HOSTGROUP_SVC_DOWNTIME",
                        command_file,
                        timestamp,
                        hostgroup_name,
                        start_time,
                        end_time,
                        fixed,
                        trigger_id,
                        duration,
                        author,
                        comment)


def del_host_downtime(
    downtime_id,
    command_file=None,
    timestamp=0
):
    """
    Deletes the host downtime entry that has an ID number matching
    the "downtime_id" argument.  If the downtime is currently in
    effect, the host will come out of scheduled downtime (as long as
    there are no other overlapping active downtime entries).
    """
    return send_command("DEL_HOST_DOWNTIME",
                        command_file,
                        timestamp,
                        downtime_id)


def del_svc_downtime(
    downtime_id,
    command_file=None,
    timestamp=0
):
    """
    Deletes the service downtime entry that has an ID number
    matching the "downtime_id" argument.  If the downtime is
    currently in effect, the service will come out of scheduled
    downtime (as long as there are no other overlapping active
    downtime entries).
    """
    return send_command("DEL_SVC_DOWNTIME",
                        command_file,
                        timestamp,
                        downtime_id)


def schedule_host_check(
    host_name,
    check_time,
    command_file=None,
    timestamp=0
):
    """
    Schedules the next active check of a particular host at
    "check_time".  The "check_time" argument is specified in time_t
    format (seconds since the UNIX epoch).  Note that the host may
    not actually be checked at the time you specify.  This could
    occur for a number of reasons: active checks are disabled on a
    program-wide or service-specific basis, the host is already
    scheduled to be checked at an earlier time, etc.  If you want to
    force the host check to occur at the time you specify, look at
    the SCHEDULE_FORCED_HOST_CHECK command.
    """
    return send_command("SCHEDULE_HOST_CHECK",
                        command_file,
                        timestamp,
                        host_name,
                        check_time)


def schedule_forced_host_check(
    host_name,
    check_time,
    command_file=None,
    timestamp=0
):
    """
    Schedules a forced active check of a particular host at
    "check_time".  The "check_time" argument is specified in time_t
    format (seconds since the UNIX epoch).   Forced checks are
    performed regardless of what time it is (e.g. timeperiod
    restrictions are ignored) and whether or not active checks are
    enabled on a host-specific or program-wide basis.
    """
    return send_command("SCHEDULE_FORCED_HOST_CHECK",
                        command_file,
                        timestamp,
                        host_name,
                        check_time)


def schedule_forced_svc_check(
    host_name,
    service_description,
    check_time,
    command_file=None,
    timestamp=0
):
    """
    Schedules a forced active check of a particular service at
    "check_time".  The "check_time" argument is specified in time_t
    format (seconds since the UNIX epoch).   Forced checks are
    performed regardless of what time it is (e.g. timeperiod
    restrictions are ignored) and whether or not active checks are
    enabled on a service-specific or program-wide basis.
    """
    return send_command("SCHEDULE_FORCED_SVC_CHECK",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        check_time)


def del_all_host_comments(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Deletes all comments assocated with a particular host.
    """
    return send_command("DEL_ALL_HOST_COMMENTS",
                        command_file,
                        timestamp,
                        host_name)


def schedule_forced_host_svc_checks(
    host_name,
    check_time,
    command_file=None,
    timestamp=0
):
    """
    Schedules a forced active check of all services associated with
    a particular host at "check_time".  The "check_time" argument is
    specified in time_t format (seconds since the UNIX epoch).
    Forced checks are performed regardless of what time it is (e.g.
    timeperiod restrictions are ignored) and whether or not active
    checks are enabled on a service-specific or program-wide basis.
    """
    return send_command("SCHEDULE_FORCED_HOST_SVC_CHECKS",
                        command_file,
                        timestamp,
                        host_name,
                        check_time)


def process_file(
    file_name,
    delete,
    command_file=None,
    timestamp=0
):
    """
    Directs Nagios to process all external commands that are found
    in the file specified by the <file_name> argument.  If the
    <delete> option is non-zero, the file will be deleted once it
    has been processes.  If the <delete> option is set to zero, the
    file is left untouched.
    """
    return send_command("PROCESS_FILE",
                        command_file,
                        timestamp,
                        file_name,
                        delete)


def change_host_check_timeperiod(
    host_name,
    check_timeperod,
    command_file=None,
    timestamp=0
):
    """
    Changes the check timeperiod for a particular host to what is
    specified by the "check_timeperiod" option.  The
    "check_timeperiod" option should be the short name of the
    timeperod that is to be used as the host check timeperiod.  The
    timeperiod must have been configured in Nagios before it was
    last (re)started.
    """
    return send_command("CHANGE_HOST_CHECK_TIMEPERIOD",
                        command_file,
                        timestamp,
                        host_name,
                        check_timeperod)


def send_custom_host_notification(
    host_name,
    options,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Allows you to send a custom host notification.  Very useful in
    dire situations, emergencies or to communicate with all admins
    that are responsible for a particular host.  When the host
    notification is sent out, the $NOTIFICATIONTYPE$ macro will be
    set to "CUSTOM".  The <options> field is a logical OR of the
    following integer values that affect aspects of the notification
    that are sent out: 0 = No option (default), 1 = Broadcast (send
    notification to all normal and all escalated contacts for the
    host), 2 = Forced (notification is sent out regardless of
    current time, whether or not notifications are enabled, etc.), 4
    = Increment current notification # for the host (this is not
    done by default for custom notifications).  The comment field
    can be used with the
    $NOTIFICATIONCOMMENT$ macro in notification commands.
    """
    return send_command("SEND_CUSTOM_HOST_NOTIFICATION",
                        command_file,
                        timestamp,
                        host_name,
                        options,
                        author,
                        comment)


def send_custom_svc_notification(
    host_name,
    service_description,
    options,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Allows you to send a custom service notification.  Very useful
    in dire situations, emergencies or to communicate with all
    admins that are responsible for a particular service.  When the
    service notification is sent out, the $NOTIFICATIONTYPE$ macro
    will be set to "CUSTOM".  The <options> field is a logical OR of
    the following integer values that affect aspects of the
    notification that are sent out: 0 = No option (default), 1 =
    Broadcast (send notification to all normal and all escalated
    contacts for the service), 2 = Forced (notification is sent out
    regardless of current time, whether or not notifications are
    enabled, etc.), 4 = Increment current notification # for the
    service(this is not done by default for custom notifications).
    The comment field can be used with the
    $NOTIFICATIONCOMMENT$ macro in notification commands.
    """
    return send_command("SEND_CUSTOM_SVC_NOTIFICATION",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        options,
                        author,
                        comment)


def change_retry_host_check_interval(
    host_name,
    service_description,
    check_interval,
    command_file=None,
    timestamp=0
):
    """
    Changes the retry check interval for a particular host.
    """
    return send_command("CHANGE_RETRY_HOST_CHECK_INTERVAL",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        check_interval)


def change_svc_check_timeperiod(
    host_name,
    service_description,
    check_timeperiod,
    command_file=None,
    timestamp=0
):
    """
    Changes the check timeperiod for a particular service to what is
    specified by the "check_timeperiod" option.  The
    "check_timeperiod" option should be the short name of the
    timeperod that is to be used as the service check timeperiod.
    The timeperiod must have been configured in Nagios before it was
    last (re)started.
    """
    return send_command("CHANGE_SVC_CHECK_TIMEPERIOD",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        check_timeperiod)


def change_host_check_timeperiod(
    host_name,
    timeperiod,
    command_file=None,
    timestamp=0
):
    """
    Changes the valid check period for the specified host.
    """
    return send_command("CHANGE_HOST_CHECK_TIMEPERIOD",
                        command_file,
                        timestamp,
                        host_name,
                        timeperiod)


def change_custom_host_var(
    host_name,
    varname,
    varvalue,
    command_file=None,
    timestamp=0
):
    """
    Changes the value of a custom host variable.
    """
    return send_command("CHANGE_CUSTOM_HOST_VAR",
                        command_file,
                        timestamp,
                        host_name,
                        varname,
                        varvalue)


def del_all_svc_comments(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Deletes all comments associated with a particular service.
    """
    return send_command("DEL_ALL_SVC_COMMENTS",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def change_custom_svc_var(
    host_name,
    service_description,
    varname,
    varvalue,
    command_file=None,
    timestamp=0
):
    """
    Changes the value of a custom service variable.
    """
    return send_command("CHANGE_CUSTOM_SVC_VAR",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        varname,
                        varvalue)


def change_custom_contact_var(
    contact_name,
    varname,
    varvalue,
    command_file=None,
    timestamp=0
):
    """
    Changes the value of a custom contact variable.
    """
    return send_command("CHANGE_CUSTOM_CONTACT_VAR",
                        command_file,
                        timestamp,
                        contact_name,
                        varname,
                        varvalue)


def enable_contact_host_notifications(
    contact_name,
    command_file=None,
    timestamp=0
):
    """
    Enables host notifications for a particular contact.
    """
    return send_command("ENABLE_CONTACT_HOST_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        contact_name)


def disable_contact_host_notifications(
    contact_name,
    command_file=None,
    timestamp=0
):
    """
    Disables host notifications for a particular contact.
    """
    return send_command("DISABLE_CONTACT_HOST_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        contact_name)


def enable_contact_svc_notifications(
    contact_name,
    command_file=None,
    timestamp=0
):
    """
    Disables service notifications for a particular contact.
    """
    return send_command("ENABLE_CONTACT_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        contact_name)


def disable_contact_svc_notifications(
    contact_name,
    command_file=None,
    timestamp=0
):
    """
    Disables service notifications for a particular contact.
    """
    return send_command("DISABLE_CONTACT_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        contact_name)


def enable_contactgroup_host_notifications(
    contactgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables host notifications for all contacts in a particular
    contactgroup.
    """
    return send_command("ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        contactgroup_name)


def disable_contactgroup_host_notifications(
    contactgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables host notifications for all contacts in a particular
    contactgroup.
    """
    return send_command("DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        contactgroup_name)


def enable_contactgroup_svc_notifications(
    contactgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables service notifications for all contacts in a particular
    contactgroup.
    """
    return send_command("ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        contactgroup_name)


def disable_contactgroup_svc_notifications(
    contactgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables service notifications for all contacts in a particular
    contactgroup.
    """
    return send_command("DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        contactgroup_name)


def enable_host_notifications(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Enables notifications for a particular host.  Notifications will
    be sent out for the host only if notifications are enabled on a
    program-wide basis as well.
    """
    return send_command("ENABLE_HOST_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        host_name)


def disable_svc_flap_detection(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Disables flap detection for the specified service.
    """
    return send_command("DISABLE_SVC_FLAP_DETECTION",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def change_svc_notification_timeperiod(
    host_name,
    service_description,
    notification_timeperiod,
    command_file=None,
    timestamp=0
):
    """
    Changes the notification timeperiod for a particular service to
    what is specified by the "notification_timeperiod" option.  The
    "notification_timeperiod" option should be the short name of the
    timeperiod that is to be used as the service notification
    timeperiod.  The timeperiod must have been configured in Nagios
    before it was last (re)started.
    """
    return send_command("CHANGE_SVC_NOTIFICATION_TIMEPERIOD",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        notification_timeperiod)


def change_contact_svc_notification_timeperiod(
    contact_name,
    notification_timeperiod,
    command_file=None,
    timestamp=0
):
    """
    Changes the service notification timeperiod for a particular
    contact to what is specified by the "notification_timeperiod"
    option.  The "notification_timeperiod" option should be the
    short name of the timeperiod that is to be used as the contact's
    service notification timeperiod.  The timeperiod must have been
    configured in Nagios before it was last (re)started.
    """
    return send_command("CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD",
                        command_file,
                        timestamp,
                        contact_name,
                        notification_timeperiod)


def change_contact_host_notification_timeperiod(
    contact_name,
    notification_timeperiod,
    command_file=None,
    timestamp=0
):
    """
    Changes the host notification timeperiod for a particular
    contact to what is specified by the "notification_timeperiod"
    option.  The "notification_timeperiod" option should be the
    short name of the timeperiod that is to be used as the contact's
    host notification timeperiod.  The timeperiod must have been
    configured in Nagios before it was last (re)started.
    """
    return send_command("CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD",
                        command_file,
                        timestamp,
                        contact_name,
                        notification_timeperiod)


def change_host_modattr(
    host_name,
    value,
    command_file=None,
    timestamp=0
):
    """
    This command changes the modified attributes value for the
    specified host.  Modified attributes values are used by Nagios
    to determine which object properties should be retained across
    program restarts.  Thus, modifying the value of the attributes
    can affect data retention.  This is an advanced option and
    should only be used by people who are intimately familiar with
    the data retention logic in Nagios.
    """
    return send_command("CHANGE_HOST_MODATTR",
                        command_file,
                        timestamp,
                        host_name,
                        value)


def change_svc_modattr(
    host_name,
    service_description,
    value,
    command_file=None,
    timestamp=0
):
    """
    This command changes the modified attributes value for the
    specified service.  Modified attributes values are used by
    Nagios to determine which object properties should be retained
    across program restarts.  Thus, modifying the value of the
    attributes can affect data retention.  This is an advanced
    option and should only be used by people who are intimately
    familiar with the data retention logic in Nagios.
    """
    return send_command("CHANGE_SVC_MODATTR",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        value)


def change_contact_modattr(
    contact_name,
    value,
    command_file=None,
    timestamp=0
):
    """
    This command changes the modified attributes value for the
    specified contact.  Modified attributes values are used by
    Nagios to determine which object properties should be retained
    across program restarts.  Thus, modifying the value of the
    attributes can affect data retention.  This is an advanced
    option and should only be used by people who are intimately
    familiar with the data retention logic in Nagios.
    """
    return send_command("CHANGE_CONTACT_MODATTR",
                        command_file,
                        timestamp,
                        contact_name,
                        value)


def change_contact_modhattr(
    contact_name,
    value,
    command_file=None,
    timestamp=0
):
    """
    This command changes the modified host attributes value for the
    specified contact.  Modified attributes values are used by
    Nagios to determine which object properties should be retained
    across program restarts.  Thus, modifying the value of the
    attributes can affect data retention.  This is an advanced
    option and should only be used by people who are intimately
    familiar with the data retention logic in Nagios.
    """
    return send_command("CHANGE_CONTACT_MODHATTR",
                        command_file,
                        timestamp,
                        contact_name,
                        value)


def change_contact_modsattr(
    contact_name,
    value,
    command_file=None,
    timestamp=0
):
    """
    This command changes the modified service attributes value for
    the specified contact.  Modified attributes values are used by
    Nagios to determine which object properties should be retained
    across program restarts.  Thus, modifying the value of the
    attributes can affect data retention.  This is an advanced
    option and should only be used by people who are intimately
    familiar with the data retention logic in Nagios.
    """
    return send_command("CHANGE_CONTACT_MODSATTR",
                        command_file,
                        timestamp,
                        contact_name,
                        value)


def disable_host_notifications(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Disables notifications for a particular host.
    """
    return send_command("DISABLE_HOST_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        host_name)


def enable_all_notifications_beyond_host(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Enables notifications for all hosts and services "beyond" (e.g.
    on all child hosts of) the specified host.  The current
    notification setting for the specified host is not affected.
    Notifications will only be sent out for these hosts and services
    if notifications are also enabled on a program-wide basis.
    """
    return send_command("ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST",
                        command_file,
                        timestamp,
                        host_name)


def disable_all_notifications_beyond_host(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Disables notifications for all hosts and services "beyond" (e.g.
    on all child hosts of) the specified host.  The current
    notification setting for the specified host is not affected.
    """
    return send_command("DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST",
                        command_file,
                        timestamp,
                        host_name)


def enable_host_and_child_notifications(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Enables notifications for the specified host, as well as all
    hosts "beyond" (e.g. on all child hosts of) the specified host.
    Notifications will only be sent out for these hosts if
    notifications are also enabled on a program-wide basis.
    """
    return send_command("ENABLE_HOST_AND_CHILD_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        host_name)


def add_svc_comment(
    host_name,
    service_description,
    persistent,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Adds a comment to a particular service.  If the "persistent"
    field is set to zero (0), the comment will be deleted the next
    time Nagios is restarted.  Otherwise, the comment will persist
    across program restarts until it is deleted manually.
    """
    return send_command("ADD_SVC_COMMENT",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        persistent,
                        author,
                        comment)


def disable_host_and_child_notifications(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Disables notifications for the specified host, as well as all
    hosts "beyond" (e.g. on all child hosts of) the specified host.
    """
    return send_command("DISABLE_HOST_AND_CHILD_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        host_name)


def set_host_notification_number(
    host_name,
    notification_number,
    command_file=None,
    timestamp=0
):
    """
    Sets the current notification number for a particular host.  A
    value of 0 indicates that no notification has yet been sent for
    the current host problem.  Useful for forcing an escalation
    (based on notification number) or replicating notification
    information in redundant monitoring environments. Notification
    numbers greater than zero have no noticeable affect on the
    notification process if the host is currently in an UP state.
    """
    return send_command("SET_HOST_NOTIFICATION_NUMBER",
                        command_file,
                        timestamp,
                        host_name,
                        notification_number)


def set_svc_notification_number(
    host_name,
    service_description,
    notification_number,
    command_file=None,
    timestamp=0
):
    """
    Sets the current notification number for a particular service.
    A value of 0 indicates that no notification has yet been sent
    for the current service problem.  Useful for forcing an
    escalation (based on notification number) or replicating
    notification information in redundant monitoring environments.
    Notification numbers greater than zero have no noticeable affect
    on the notification process if the service is currently in an OK
    state.
    """
    return send_command("SET_SVC_NOTIFICATION_NUMBER",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        notification_number)


def enable_service_freshness_checks(
    command_file=None,
    timestamp=0
):
    """
    Enables freshness checks of all services on a program-wide
    basis.  Individual services that have freshness checks disabled
    will not be checked for freshness.
    """
    return send_command("ENABLE_SERVICE_FRESHNESS_CHECKS",
                        command_file,
                        timestamp,
                        )


def enable_host_freshness_checks(
    command_file=None,
    timestamp=0
):
    """
    Enables freshness checks of all hosts on a program-wide basis.
    Individual hosts that have freshness checks disabled will not be
    checked for freshness.
    """
    return send_command("ENABLE_HOST_FRESHNESS_CHECKS",
                        command_file,
                        timestamp,
                        )


def disable_service_freshness_checks(
    command_file=None,
    timestamp=0
):
    """
    Disables freshness checks of all services on a program-wide
    basis.
    """
    return send_command("DISABLE_SERVICE_FRESHNESS_CHECKS",
                        command_file,
                        timestamp,
                        )


def disable_host_freshness_checks(
    command_file=None,
    timestamp=0
):
    """
    Disables freshness checks of all hosts on a program-wide basis.
    """
    return send_command("DISABLE_HOST_FRESHNESS_CHECKS",
                        command_file,
                        timestamp,
                        )


def schedule_and_propagate_triggered_host_downtime(
    host_name,
    start_time,
    end_time,
    fixed,
    trigger_id,
    duration,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Schedules downtime for a specified host and all of its children
    (hosts).  If the "fixed" argument is set to one (1), downtime
    will start and end at the times specified by the "start" and
    "end" arguments.  Otherwise, downtime will begin between the
    "start" and "end" times and last for "duration" seconds.  The
    "start" and "end" arguments are specified in time_t format
    (seconds since the UNIX epoch).  Downtime for child hosts are
    all set to be triggered by the downtime for the specified
    (parent) host.  The specified (parent) host downtime can be
    triggered by another downtime entry if the "trigger_id" is set
    to the ID of another scheduled downtime entry.  Set the
    "trigger_id" argument to zero (0) if the downtime for the
    specified (parent) host should not be triggered by another
    downtime entry.
    """
    return send_command("SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME",
                        command_file,
                        timestamp,
                        host_name,
                        start_time,
                        end_time,
                        fixed,
                        trigger_id,
                        duration,
                        author,
                        comment)


def schedule_and_propagate_host_downtime(
    host_name,
    start_time,
    end_time,
    fixed,
    trigger_id,
    duration,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Schedules downtime for a specified host and all of its children
    (hosts).  If the "fixed" argument is set to one (1), downtime
    will start and end at the times specified by the "start" and
    "end" arguments.  Otherwise, downtime will begin between the
    "start" and "end" times and last for "duration" seconds.  The
    "start" and "end" arguments are specified in time_t format
    (seconds since the UNIX epoch).  The specified (parent) host
    downtime can be triggered by another downtime entry if the
    "trigger_id" is set to the ID of another scheduled downtime
    entry.  Set the "trigger_id" argument to zero (0) if the
    downtime for the specified (parent) host should not be triggered
    by another downtime entry.
    """
    return send_command("SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME",
                        command_file,
                        timestamp,
                        host_name,
                        start_time,
                        end_time,
                        fixed,
                        trigger_id,
                        duration,
                        author,
                        comment)


def schedule_svc_check(
    host_name,
    service_description,
    check_time,
    command_file=None,
    timestamp=0
):
    """
    Schedules the next active check of a specified service at
    "check_time".  The "check_time" argument is specified in time_t
    format (seconds since the UNIX epoch).  Note that the service
    may not actually be checked at the time you specify.  This could
    occur for a number of reasons: active checks are disabled on a
    program-wide or service-specific basis, the service is already
    scheduled to be checked at an earlier time, etc.  If you want to
    force the service check to occur at the time you specify, look
    at the SCHEDULE_FORCED_SVC_CHECK command.
    """
    return send_command("SCHEDULE_SVC_CHECK",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        check_time)


def del_host_comment(
    comment_id,
    command_file=None,
    timestamp=0
):
    """
    Deletes a host comment.  The id number of the comment that is to
    be deleted must be specified.
    """
    return send_command("DEL_HOST_COMMENT",
                        command_file,
                        timestamp,
                        comment_id)


def schedule_host_svc_checks(
    host_name,
    check_time,
    command_file=None,
    timestamp=0
):
    """
    Schedules the next active check of all services on a particular
    host at "check_time".  The "check_time" argument is specified in
    time_t format (seconds since the UNIX epoch).  Note that the
    services may not actually be checked at the time you specify.
    This could occur for a number of reasons: active checks are
    disabled on a program-wide or service-specific basis, the
    services are already scheduled to be checked at an earlier time,
    etc.  If you want to force the service checks to occur at the
    time you specify, look at the SCHEDULE_FORCED_HOST_SVC_CHECKS
    command.
    """
    return send_command("SCHEDULE_HOST_SVC_CHECKS",
                        command_file,
                        timestamp,
                        host_name,
                        check_time)


def save_state_information(
    command_file=None,
    timestamp=0
):
    """
    Causes Nagios to save all current monitoring status information
    to the state retention file.  Normally, state retention
    information is saved before the Nagios process shuts down and
    (potentially) at regularly scheduled intervals.  This command
    allows you to force Nagios to save this information to the state
    retention file immediately.  This does not affect the current
    status information in the Nagios process.
    """
    return send_command("SAVE_STATE_INFORMATION",
                        command_file,
                        timestamp,
                        )


def read_state_information(
    command_file=None,
    timestamp=0
):
    """
    Causes Nagios to load all current monitoring status information
    from the state retention file.  Normally, state retention
    information is loaded when the Nagios process starts up and
    before it starts monitoring.  WARNING: This command will cause
    Nagios to discard all current monitoring status information and
    use the information stored in state retention file!  Use with
    care.
    """
    return send_command("READ_STATE_INFORMATION",
                        command_file,
                        timestamp,
                        )


def enable_host_svc_checks(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Enables active checks of all services on the specified host.
    """
    return send_command("ENABLE_HOST_SVC_CHECKS",
                        command_file,
                        timestamp,
                        host_name)


def disable_host_svc_checks(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Enables active checks of all services on the specified host.
    """
    return send_command("DISABLE_HOST_SVC_CHECKS",
                        command_file,
                        timestamp,
                        host_name)


def enable_host_svc_notifications(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Enables notifications for all services on the specified host.
    Note that notifications will not be sent out if notifications
    are disabled on a program-wide basis.
    """
    return send_command("ENABLE_HOST_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        host_name)


def disable_host_svc_notifications(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Disables notifications for all services on the specified host.
    """
    return send_command("DISABLE_HOST_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        host_name)


def delay_svc_notification(
    host_name,
    service_description,
    notification_time,
    command_file=None,
    timestamp=0
):
    """
    Delays the next notification for a parciular service until
    "notification_time".  The "notification_time" argument is
    specified in time_t format (seconds since the UNIX epoch).  Note
    that this will only have an affect if the service stays in the
    same problem state that it is currently in.  If the service
    changes to another state, a new notification may go out before
    the time you specify in the "notification_time" argument.
    """
    return send_command("DELAY_SVC_NOTIFICATION",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        notification_time)


def delay_host_notification(
    host_name,
    notification_time,
    command_file=None,
    timestamp=0
):
    """
    Delays the next notification for a parciular service until
    "notification_time".  The "notification_time" argument is
    specified in time_t format (seconds since the UNIX epoch).  Note
    that this will only have an affect if the service stays in the
    same problem state that it is currently in.  If the service
    changes to another state, a new notification may go out before
    the time you specify in the "notification_time" argument.
    """
    return send_command("DELAY_HOST_NOTIFICATION",
                        command_file,
                        timestamp,
                        host_name,
                        notification_time)


def acknowledge_host_problem(
    host_name,
    sticky,
    notify,
    persistent,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Allows you to acknowledge the current problem for the specified
    host.  By acknowledging the current problem, future
    notifications (for the same host state) are disabled.  If the
    "sticky" option is set to two (2), the acknowledgement will
    remain until the host returns to an UP state.  Otherwise the
    acknowledgement will automatically be removed when the host
    changes state.  If the "notify" option is set to one (1), a
    notification will be sent out to contacts indicating that the
    current host problem has been acknowledged.  If the "persistent"
    option is set to one (1), the comment associated with the
    acknowledgement will survive across restarts of the Nagios
    process.  If not, the comment will be deleted the next time
    Nagios restarts.
    """
    return send_command("ACKNOWLEDGE_HOST_PROBLEM",
                        command_file,
                        timestamp,
                        host_name,
                        sticky,
                        notify,
                        persistent,
                        author,
                        comment)


def del_svc_comment(
    comment_id,
    command_file=None,
    timestamp=0
):
    """
    Deletes a service comment.  The id number of the comment that is
    to be deleted must be specified.
    """
    return send_command("DEL_SVC_COMMENT",
                        command_file,
                        timestamp,
                        comment_id)


def acknowledge_svc_problem(
    host_name,
    service_description,
    sticky,
    notify,
    persistent,
    author,
    comment,
    command_file=None,
    timestamp=0
):
    """
    Allows you to acknowledge the current problem for the specified
    service.  By acknowledging the current problem, future
    notifications (for the same servicestate) are disabled.  If the
    "sticky" option is set to two (2), the acknowledgement will
    remain until the service returns to an OK state.  Otherwise the
    acknowledgement will automatically be removed when the service
    changes state.  If the "notify" option is set to one (1), a
    notification will be sent out to contacts indicating that the
    current service problem has been acknowledged.  If the
    "persistent" option is set to one (1), the comment associated
    with the acknowledgement will survive across restarts of the
    Nagios process.  If not, the comment will be deleted the next
    time Nagios restarts.
    """
    return send_command("ACKNOWLEDGE_SVC_PROBLEM",
                        command_file,
                        timestamp,
                        host_name,
                        service_description,
                        sticky,
                        notify,
                        persistent,
                        author,
                        comment)


def start_executing_svc_checks(
    command_file=None,
    timestamp=0
):
    """
    Enables active checks of services on a program-wide basis.
    """
    return send_command("START_EXECUTING_SVC_CHECKS",
                        command_file,
                        timestamp,
                        )


def stop_executing_svc_checks(
    command_file=None,
    timestamp=0
):
    """
    Disables active checks of services on a program-wide basis.
    """
    return send_command("STOP_EXECUTING_SVC_CHECKS",
                        command_file,
                        timestamp,
                        )


def start_accepting_passive_svc_checks(
    command_file=None,
    timestamp=0
):
    """
    Enables passive service checks on a program-wide basis.
    """
    return send_command("START_ACCEPTING_PASSIVE_SVC_CHECKS",
                        command_file,
                        timestamp,
                        )


def stop_accepting_passive_svc_checks(
    command_file=None,
    timestamp=0
):
    """
    Disables passive service checks on a program-wide basis.
    """
    return send_command("STOP_ACCEPTING_PASSIVE_SVC_CHECKS",
                        command_file,
                        timestamp,
                        )


def enable_passive_svc_checks(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Enables passive checks for the specified service.
    """
    return send_command("ENABLE_PASSIVE_SVC_CHECKS",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def disable_passive_svc_checks(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Disables passive checks for the specified service.
    """
    return send_command("DISABLE_PASSIVE_SVC_CHECKS",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def enable_event_handlers(
    command_file=None,
    timestamp=0
):
    """
    Enables host and service event handlers on a program-wide basis.
    """
    return send_command("ENABLE_EVENT_HANDLERS",
                        command_file,
                        timestamp,
                        )


def disable_event_handlers(
    command_file=None,
    timestamp=0
):
    """
    Disables host and service event handlers on a program-wide
    basis.
    """
    return send_command("DISABLE_EVENT_HANDLERS",
                        command_file,
                        timestamp,
                        )


def enable_host_event_handler(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Enables the event handler for the specified host.
    """
    return send_command("ENABLE_HOST_EVENT_HANDLER",
                        command_file,
                        timestamp,
                        host_name)


def enable_svc_check(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Enables active checks for a particular service.
    """
    return send_command("ENABLE_SVC_CHECK",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def disable_host_event_handler(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Disables the event handler for the specified host.
    """
    return send_command("DISABLE_HOST_EVENT_HANDLER",
                        command_file,
                        timestamp,
                        host_name)


def enable_svc_event_handler(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Enables the event handler for the specified service.
    """
    return send_command("ENABLE_SVC_EVENT_HANDLER",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def disable_svc_event_handler(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Disables the event handler for the specified service.
    """
    return send_command("DISABLE_SVC_EVENT_HANDLER",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def enable_host_check(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Enables (regularly scheduled and on-demand) active checks of the
    specified host.
    """
    return send_command("ENABLE_HOST_CHECK",
                        command_file,
                        timestamp,
                        host_name)


def disable_host_check(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Disables (regularly scheduled and on-demand) active checks of
    the specified host.
    """
    return send_command("DISABLE_HOST_CHECK",
                        command_file,
                        timestamp,
                        host_name)


def start_obsessing_over_svc_checks(
    command_file=None,
    timestamp=0
):
    """
    Enables processing of service checks via the OCSP command on a
    program-wide basis.
    """
    return send_command("START_OBSESSING_OVER_SVC_CHECKS",
                        command_file,
                        timestamp,
                        )


def stop_obsessing_over_svc_checks(
    command_file=None,
    timestamp=0
):
    """
    Disables processing of service checks via the OCSP command on a
    program-wide basis.
    """
    return send_command("STOP_OBSESSING_OVER_SVC_CHECKS",
                        command_file,
                        timestamp,
                        )


def start_obsessing_over_host_checks(
    command_file=None,
    timestamp=0
):
    """
    Enables processing of host checks via the OCHP command on a
    program-wide basis.
    """
    return send_command("START_OBSESSING_OVER_HOST_CHECKS",
                        command_file,
                        timestamp,
                        )


def stop_obsessing_over_host_checks(
    command_file=None,
    timestamp=0
):
    """
    Disables processing of host checks via the OCHP command on a
    program-wide basis.
    """
    return send_command("STOP_OBSESSING_OVER_HOST_CHECKS",
                        command_file,
                        timestamp,
                        )


def start_obsessing_over_host(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Enables processing of host checks via the OCHP command for the
    specified host.
    """
    return send_command("START_OBSESSING_OVER_HOST",
                        command_file,
                        timestamp,
                        host_name)


def disable_svc_check(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Disables active checks for a particular service.
    """
    return send_command("DISABLE_SVC_CHECK",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def stop_obsessing_over_host(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Disables processing of host checks via the OCHP command for the
    specified host.
    """
    return send_command("STOP_OBSESSING_OVER_HOST",
                        command_file,
                        timestamp,
                        host_name)


def start_obsessing_over_svc(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Enables processing of service checks via the OCSP command for
    the specified service.
    """
    return send_command("START_OBSESSING_OVER_SVC",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def stop_obsessing_over_svc(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Disables processing of service checks via the OCSP command for
    the specified service.
    """
    return send_command("STOP_OBSESSING_OVER_SVC",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def enable_failure_prediction(
    command_file=None,
    timestamp=0
):
    """
    Enables failure prediction on a program-wide basis.  This
    feature is not currently implemented in Nagios.
    """
    return send_command("ENABLE_FAILURE_PREDICTION",
                        command_file,
                        timestamp,
                        )


def disable_failure_prediction(
    command_file=None,
    timestamp=0
):
    """
    Disables failure prediction on a program-wide basis.  This
    feature is not currently implemented in Nagios.
    """
    return send_command("DISABLE_FAILURE_PREDICTION",
                        command_file,
                        timestamp,
                        )


def enable_performance_data(
    command_file=None,
    timestamp=0
):
    """
    Enables the processing of host and service performance data on a
    program-wide basis.
    """
    return send_command("ENABLE_PERFORMANCE_DATA",
                        command_file,
                        timestamp,
                        )


def disable_performance_data(
    command_file=None,
    timestamp=0
):
    """
    Disables the processing of host and service performance data on
    a program-wide basis.
    """
    return send_command("DISABLE_PERFORMANCE_DATA",
                        command_file,
                        timestamp,
                        )


def start_executing_host_checks(
    command_file=None,
    timestamp=0
):
    """
    Enables active host checks on a program-wide basis.
    """
    return send_command("START_EXECUTING_HOST_CHECKS",
                        command_file,
                        timestamp,
                        )


def stop_executing_host_checks(
    command_file=None,
    timestamp=0
):
    """
    Disables active host checks on a program-wide basis.
    """
    return send_command("STOP_EXECUTING_HOST_CHECKS",
                        command_file,
                        timestamp,
                        )


def start_accepting_passive_host_checks(
    command_file=None,
    timestamp=0
):
    """
    Enables acceptance and processing of passive host checks on a
    program-wide basis.
    """
    return send_command("START_ACCEPTING_PASSIVE_HOST_CHECKS",
                        command_file,
                        timestamp,
                        )


def disable_notifications(
    command_file=None,
    timestamp=0
):
    """
    Disables host and service notifications on a program-wide basis.
    """
    return send_command("DISABLE_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        )


def stop_accepting_passive_host_checks(
    command_file=None,
    timestamp=0
):
    """
    Disables acceptance and processing of passive host checks on a
    program-wide basis.
    """
    return send_command("STOP_ACCEPTING_PASSIVE_HOST_CHECKS",
                        command_file,
                        timestamp,
                        )


def enable_passive_host_checks(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Enables acceptance and processing of passive host checks for the
    specified host.
    """
    return send_command("ENABLE_PASSIVE_HOST_CHECKS",
                        command_file,
                        timestamp,
                        host_name)


def disable_passive_host_checks(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Disables acceptance and processing of passive host checks for
    the specified host.
    """
    return send_command("DISABLE_PASSIVE_HOST_CHECKS",
                        command_file,
                        timestamp,
                        host_name)


def enable_flap_detection(
    command_file=None,
    timestamp=0
):
    """
    Enables host and service flap detection on a program-wide basis.
    """
    return send_command("ENABLE_FLAP_DETECTION",
                        command_file,
                        timestamp,
                        )


def disable_flap_detection(
    command_file=None,
    timestamp=0
):
    """
    Disables host and service flap detection on a program-wide
    basis.
    """
    return send_command("DISABLE_FLAP_DETECTION",
                        command_file,
                        timestamp,
                        )


def enable_host_flap_detection(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Enables flap detection for the specified host.  In order for the
    flap detection algorithms to be run for the host, flap detection
    must be enabled on a program-wide basis as well.
    """
    return send_command("ENABLE_HOST_FLAP_DETECTION",
                        command_file,
                        timestamp,
                        host_name)


def enable_svc_flap_detection(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Enables flap detection for the specified service.  In order for
    the flap detection algorithms to be run for the service, flap
    detection must be enabled on a program-wide basis as well.
    """
    return send_command("ENABLE_SVC_FLAP_DETECTION",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def disable_host_flap_detection(
    host_name,
    command_file=None,
    timestamp=0
):
    """
    Disables flap detection for the specified host.
    """
    return send_command("DISABLE_HOST_FLAP_DETECTION",
                        command_file,
                        timestamp,
                        host_name)


def disable_service_flap_detection(
    host_name,
    service_description,
    command_file=None,
    timestamp=0
):
    """
    Disables flap detection for the specified service.
    """
    return send_command("DISABLE_SERVICE_FLAP_DETECTION",
                        command_file,
                        timestamp,
                        host_name,
                        service_description)


def enable_hostgroup_svc_notifications(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables notifications for all services that are associated with
    hosts in a particular hostgroup.  This does not enable
    notifications for the hosts in the hostgroup - see the
    ENABLE_HOSTGROUP_HOST_NOTIFICATIONS command for that.  In order
    for notifications to be sent out for these services,
    notifications must be enabled on a program-wide basis as well.
    """
    return send_command("ENABLE_HOSTGROUP_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def enable_notifications(
    command_file=None,
    timestamp=0
):
    """
    Enables host and service notifications on a program-wide basis.
    """
    return send_command("ENABLE_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        )


def disable_hostgroup_svc_notifications(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables notifications for all services associated with hosts in
    a particular hostgroup.  This does not disable notifications for
    the hosts in the hostgroup - see the
    DISABLE_HOSTGROUP_HOST_NOTIFICATIONS command for that.
    """
    return send_command("DISABLE_HOSTGROUP_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def enable_hostgroup_host_notifications(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables notifications for all hosts in a particular hostgroup.
    This does not enable notifications for the services associated
    with the hosts in the hostgroup - see the
    ENABLE_HOSTGROUP_SVC_NOTIFICATIONS command for that.  In order
    for notifications to be sent out for these hosts, notifications
    must be enabled on a program-wide basis as well.
    """
    return send_command("ENABLE_HOSTGROUP_HOST_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def disable_hostgroup_host_notifications(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables notifications for all hosts in a particular hostgroup.
    This does not disable notifications for the services associated
    with the hosts in the hostgroup - see the
    DISABLE_HOSTGROUP_SVC_NOTIFICATIONS command for that.
    """
    return send_command("DISABLE_HOSTGROUP_HOST_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def enable_hostgroup_svc_checks(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables active checks for all services associated with hosts in
    a particular hostgroup.
    """
    return send_command("ENABLE_HOSTGROUP_SVC_CHECKS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def disable_hostgroup_svc_checks(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables active checks for all services associated with hosts in
    a particular hostgroup.
    """
    return send_command("DISABLE_HOSTGROUP_SVC_CHECKS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def enable_hostgroup_host_checks(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables active checks for all hosts in a particular hostgroup.
    """
    return send_command("ENABLE_HOSTGROUP_HOST_CHECKS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def disable_hostgroup_host_checks(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables active checks for all hosts in a particular hostgroup.
    """
    return send_command("DISABLE_HOSTGROUP_HOST_CHECKS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def enable_hostgroup_passive_host_checks(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables passive checks for all hosts in a particular hostgroup.
    """
    return send_command("ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def disable_hostgroup_passive_host_checks(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables passive checks for all hosts in a particular hostgroup.
    """
    return send_command("DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def enable_hostgroup_passive_svc_checks(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables passive checks for all services associated with hosts in
    a particular hostgroup.
    """
    return send_command("ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def restart_program(
    command_file=None,
    timestamp=0
):
    """
    Restarts the Nagios process.
    """
    return send_command("RESTART_PROGRAM",
                        command_file,
                        timestamp,
                        )


def disable_hostgroup_passive_svc_checks(
    hostgroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables passive checks for all services associated with hosts
    in a particular hostgroup.
    """
    return send_command("DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS",
                        command_file,
                        timestamp,
                        hostgroup_name)


def enable_servicegroup_svc_notifications(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables notifications for all services that are members of a
    particular servicegroup.  In order for notifications to be sent
    out for these services, notifications must also be enabled on a
    program-wide basis.
    """
    return send_command("ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        servicegroup_name)


def disable_servicegroup_svc_notifications(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables notifications for all services that are members of a
    particular servicegroup.
    """
    return send_command("DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        servicegroup_name)


def enable_servicegroup_host_notifications(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables notifications for all hosts that have services that are
    members of a particular servicegroup.  In order for
    notifications to be sent out for these hosts, notifications must
    also be enabled on a program-wide basis.
    """
    return send_command("ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        servicegroup_name)


def disable_servicegroup_host_notifications(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables notifications for all hosts that have services that are
    members of a particular servicegroup.
    """
    return send_command("DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS",
                        command_file,
                        timestamp,
                        servicegroup_name)


def enable_servicegroup_svc_checks(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables active checks for all services in a particular
    servicegroup.
    """
    return send_command("ENABLE_SERVICEGROUP_SVC_CHECKS",
                        command_file,
                        timestamp,
                        servicegroup_name)


def disable_servicegroup_svc_checks(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables active checks for all services in a particular
    servicegroup.
    """
    return send_command("DISABLE_SERVICEGROUP_SVC_CHECKS",
                        command_file,
                        timestamp,
                        servicegroup_name)


def enable_servicegroup_host_checks(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables active checks for all hosts that have services that are
    members of a particular hostgroup.
    """
    return send_command("ENABLE_SERVICEGROUP_HOST_CHECKS",
                        command_file,
                        timestamp,
                        servicegroup_name)


def disable_servicegroup_host_checks(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Disables active checks for all hosts that have services that are
    members of a particular hostgroup.
    """
    return send_command("DISABLE_SERVICEGROUP_HOST_CHECKS",
                        command_file,
                        timestamp,
                        servicegroup_name)


def enable_servicegroup_passive_svc_checks(
    servicegroup_name,
    command_file=None,
    timestamp=0
):
    """
    Enables the acceptance and processing of passive checks for all
    services in a particular servicegroup.
    """
    return send_command("ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS",
                        command_file,
                        timestamp,
                        servicegroup_name)
