on_error () {
    local ret=$?
    local i=0
    local argv_offset=0
    local FRAMES=${#BASH_SOURCE[@]}
    local extdebug=$(shopt -q extdebug; echo $?)

    echo >&2 "Traceback (most recent call last):"
    for ((frame=FRAMES-2; frame >= 0; frame--)); do
        local lineno=${BASH_LINENO[frame]}

        printf >&2 '  File "%s", line %d, in %s\n' "${BASH_SOURCE[frame+1]}" "$lineno" "${FUNCNAME[frame+1]}"
        if [[ $extdebug -eq 0 && $i -ne 0 ]]; then
            # Courtesy http://www.runscripts.com/support/guides/scripting/bash/debugging-bash/stack-trace
            declare argv=()
            declare argc
            declare frame_argc

            for ((frame_argc=${BASH_ARGC[frame]},frame_argc--,argc=0; frame_argc >= 0; argc++, frame_argc--)) ; do
                argv[argc]=${BASH_ARGV[argv_offset+frame_argc]}
                case "${argv[argc]}" in
                    *[[:space:]]*) argv[argc]="'${argv[argc]}'" ;;
                esac
            done
            argv_offset=$((argv_offset + ${BASH_ARGC[frame]}))
            echo >&2 "    ${FUNCNAME[i]} ${argv[*]}"
        else
            sed >&2 -n "${lineno}s/^[ 	]*/    /p" "${BASH_SOURCE[frame+1]}"
        fi
    done
    printf >&2 "Exiting with %d\n" "$ret"
    exit $ret
}

on_exit () {
    ret=$?
    case $ret in
        0)
            ;;
        *)
            echo >&2 "Exiting with $ret from a shell command"
            ;;
    esac
}

case "$BASH_VERSION" in
    '')
        trap on_exit EXIT
        ;;
    *)
        set -o errtrace
        if [[ ${BASH_VERSINFO[0]} -ge 3 ]]; then
            shopt -s extdebug
        fi
        trap on_error ERR
        ;;
esac
