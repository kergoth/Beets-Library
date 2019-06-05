# shellcheck disable=SC2154,SC2001,SC2119,SC2120,SC2034

TAB="$(printf '\t')"

# Commonly used metadata variables
tracknum_vars="track tracknumber tracktotal totaltracks"
discnum_vars="disc discnumber disctotal totaldiscs"
md_vars="$tracknum_vars $discnum_vars \
         itunesadvisory rtng \
         releasetype \
         genre albumgenre \
         year originalyear \
         media tmed \
         musicbrainz_album_id \
         artist album_artist artists \
         title album compilation discsubtitle setsubtitle"
known_releasetypes="album compilation ep live other remix \
                    single soundtrack spokenword"

die() {
    ret="$1"
    shift
    fmt="$1"
    shift
    # shellcheck disable=SC2059
    printf >&2 "Error: $fmt\\n" "$@"
    exit "$ret"
}

fn_sanitize() {
    sanitize_fn="$1"
    shift
    # shellcheck disable=SC1003
    echo "$sanitize_fn" | tr -d '™ ' | sed -e "s/^\\.//; s/ :/:/g; $*" | unidecode | tr ':/\\|*' '∶／＼￨✱'
}

get_metadata() {
    fn="$1"
    shift

    case "$fn" in
        *.ogg)
            get_metadata_exif "$fn" "$@"
            return $?
            ;;
        *.m4a)
            if echo "$@" | grep -qw itunesadvisory; then
                (
                    eval "$(get_metadata_exif "$fn" rating)"
                    case "$rating" in
                        Clean)
                            echo 'itunesadvisory="2"'
                            ;;
                        Explicit)
                            echo 'itunesadvisory="1"'
                            ;;
                    esac
                )
            fi
            ;;
    esac

    pat="$(echo "$@" | sed -e 's/  */ /g')"
    # ffprobe -v quiet -show_format -show_streams -of flat=s=_ -show_entries format_tags "$fn"
    ffprobe -v quiet -show_format -of flat=s=_ -show_entries format_tags "$fn" \
        | cut -d_ -f2- \
        | sed -e 's/^tags_//' \
        | while IFS="=" read -r key value; do
            key="$(printf '%s\n' "$key" | tr "[:upper:]" "[:lower:]")"
            if [ -n "$pat" ]; then
                case " $pat " in
                    *\ $key\ *) ;;

                    *)
                        continue
                        ;;
                esac
            fi
            printf '%s=%s\n' "$key" "$value"
        done
}

get_metadata_exif() {
    fn="$1"
    shift
    pat="$(echo "$@" | sed -e 's/  */ /g')"
    exiftool -S "$fn" \
        | sed -e 's/: /=/' \
        | while IFS="=" read -r key value; do
            if [ -z "$key" ]; then
                continue
            fi
            case "$key" in
                *\ *)
                    key="$(echo "$key" | tr -d " ")"
                    ;;
                Albumartist)
                    key="Album_Artist"
                    ;;
            esac
            # shellcheck disable=SC1003
            key="$(printf '%s\n' "$key" | tr ".:/-#=\`" "_______" | tr "[:upper:]" "[:lower:]" | tr -d '\')"
            if [ -n "$pat" ]; then
                case " $pat " in
                    *\ $key\ *) ;;

                    *)
                        continue
                        ;;
                esac
            fi
            # shellcheck disable=SC2016
            value="$(printf '%s\n' "$value" | sed -e 's/"/\\"/g; s/\\$//; s/`/\\`/g')"
            printf '%s="%s"\n' "$key" "$value"
        done
}

eval_metadata() {
    # Useful for debugging shell syntax errors when eval'ing the metadata
    # get_metadata "$@" | while read -r line; do
    #     ( eval "$line" ) >/dev/null 2>&1 || die 1 'Unable to eval `%s`' "$line"
    # done
    fn="$1"
    shift

    unset "$@"
    eval "$(get_metadata "$fn" "$@")"
    if [ -z "$title" ] && [ -z "$track" ] && [ -z "$tracknumber" ]; then
        eval "$(get_metadata_exif "$fn" "$@")"
    fi

    # Fallbacks for tag differences between formats
    if [ -z "$artist" ]; then
        artist="$artists"
    fi
    if [ -z "$year" ]; then
        originalyear="$year"
    fi
    if [ -z "$media" ]; then
        media="$tmed"
    fi

    # Ensure that track, tracknumber, and tracktotal are set if possible
    if [ -z "$tracktotal" ] && [ -n "$totaltracks" ]; then
        tracktotal="$totaltracks"
    fi
    case "$track" in
        */*)
            tracknumber="${track%/*}"
            tracktotal="${track##*/}"
            if [ "$tracktotal" = "0" ]; then
                tracktotal=
                track="$tracknumber"
            fi
            ;;
        '')
            if [ -n "$tracknumber" ]; then
                track="$tracknumber"
                if [ -n "$tracktotal" ] && [ "$tracktotal" != "0" ]; then
                    track="$tracknumber/$tracktotal"
                fi
            fi
            ;;
        *)
            tracknumber="$track"
            if [ -n "$tracktotal" ] && [ "$tracktotal" != "0" ]; then
                track="$track/$tracktotal"
            fi
            ;;
    esac
    if [ "$tracktotal" = "0" ]; then
        tracktotal=
    fi
    if [ "$tracknumber" = "0" ]; then
        tracknumber=
    fi

    # Ensure that disc, discnumber, and disctotal are set if possible
    if [ -z "$disctotal" ] && [ -n "$totaldiscs" ]; then
        disctotal="$totaldiscs"
    fi
    case "$disc" in
        */*)
            discnumber="${disc%/*}"
            disctotal="${disc##*/}"
            if [ "$disctotal" = "0" ]; then
                disctotal=
                disc="$discnumber"
            fi
            ;;
        '')
            if [ -n "$discnumber" ]; then
                disc="$discnumber"
                if [ -n "$disctotal" ] && [ "$disctotal" != "0" ]; then
                    disc="$discnumber/$disctotal"
                fi
            fi
            ;;
        *)
            discnumber="$disc"
            if [ -n "$disctotal" ] && [ "$disctotal" != "0" ]; then
                disc="$disc/$disctotal"
            fi
            ;;
    esac
    if [ "$disctotal" = "0" ]; then
        disctotal=
    fi
}

eval_common_metadata() {
    fn="$1"
    shift
    if [ $# -eq 0 ]; then
        # shellcheck disable=SC2086
        set -- $md_vars
    fi
    eval_metadata "$fn" "$@"
}

get_new_filename() {
    if [ "$1" = "-d" ]; then
        separate_disc_folders=1
        shift
    else
        separate_disc_folders=0
    fi
    if [ "$1" = "-t" ]; then
        suffix_the=1
        shift
    else
        suffix_the=0
    fi

    fn="$1"
    source_dir="$2"
    if [ -n "$album" ] && [ "$album" != "[non-album tracks]" ]; then
        albumdir="$album"
        fn_tracknumber="$tracknumber"
    else
        albumdir="[non-album tracks]"
        fn_tracknumber=
    fi

    if { [ -n "$disctotal" ] && [ "$disctotal" != 1 ]; } \
        || { [ -n "$discnumber" ] && [ "$discnumber" -gt 1 ]; }; then
        if [ -z "$discsubtitle" ]; then
            discsubtitle="$setsubtitle"
            case "$setsubtitle" in
                */*)
                    if [ "${setsubtitle%/*}" = "${setsubtitle#*/}" ]; then
                        discsubtitle="${setsubtitle%/*}"
                    fi
                    ;;
            esac
        fi
        if [ -n "$discnumber" ]; then
            if [ $separate_disc_folders -eq 0 ]; then
                if [ -n "$tracknumber" ]; then
                    fn_tracknumber="$discnumber-$tracknumber"
                else
                    fn_tracknumber="$discnumber-0"
                fi
            elif [ -n "$discnumber" ]; then
                if [ -n "$discsubtitle" ]; then
                    albumdir="$albumdir Disc $discnumber: $discsubtitle"
                else
                    albumdir="$albumdir Disc $discnumber"
                fi
            fi
        fi
    fi

    if [ -n "$fn_tracknumber" ]; then
        if [ "$tracknumber" != 1 ] || [ -z "$tracktotal" ] || [ "$tracktotal" != 1 ]; then
            newfn="$fn_tracknumber - "
        else
            newfn=
        fi
    else
        newfn=
    fi

    if { [ -n "$compilation" ] && [ "$compilation" = 1 ]; } \
        || { [ -n "$album_artist" ] && echo "$album_artist" | grep -qi '^various'; }; then
        newfn="$newfn$artist - "
        compilation=1
    fi

    if [ -z "$title" ]; then
        if [ -n "$tracknumber" ]; then
            title="Track $tracknumber"
        else
            title="[unknown]"
        fi
    fi

    newfn="$newfn$title.${fn##*.}"

    if [ -n "$compilation" ] && [ "$compilation" -eq 1 ]; then
        artistdir=Compilations
    elif [ -n "$album_artist" ]; then
        artistdir="$album_artist"
    elif [ -n "$artist" ]; then
        artistdir="$artist"
    else
        artistdir="[unknown]"
    fi
    artistdir="$(fn_sanitize "$artistdir")"
    albumdir="$(fn_sanitize "$albumdir" "s/:$//")"
    # Special case. Soundtracks are generally a movie name, which we shouldn't
    # be changing, or it won't line up with the movie name anymore.
    genre="$(get_genre "$fn")"
    if [ $suffix_the -eq 1 ] && [ "$genre" != Soundtrack ]; then
        albumdir="$(echo "$albumdir" | sed -e 's/^The \(.*\)/\1, The/')"
    fi
    destdir="$artistdir/$albumdir"
    newfn="$(fn_sanitize "$newfn" "s/:$//")"
    destfn="$source_dir/$destdir/$newfn"
    echo "$destfn"
}

get_album_track_total_indiv_discs() {
    if [ -n "$tracktotal" ]; then
        echo "$tracktotal"
    else
        return 1
    fi
}

music_find() {
    finddir="$1"
    shift
    find -L "$finddir" \( -type f -o -type l \) -not -name ._\* \( -iname \*.flac -o -iname \*mp3 -o -iname \*.m4a -o -iname \*.ogg -o -iname \*.dsf \) "$@"
}

nonmusic_find() {
    finddir="$1"
    shift
    find -L "$finddir" \( -type f -o -type l \) -not \( -name ._\* -o -iname \*.flac -o -iname \*mp3 -o -iname \*.m4a -o -iname \*.ogg -o -iname \*.dsf \) "$@"
}

# We need to get the total tracks for all discs to get a true total
get_album_track_total() {
    file_count="$(music_find "$1" | wc -l)"
    music_find "$1" \
        | (
            total=0
            while read -r fn; do
                eval_common_metadata "$fn"

                existing_total="$(eval "printf '%s' \"\${total$discnumber}\"")"
                if [ -z "$existing_total" ]; then
                    if [ -n "$tracktotal" ]; then
                        eval "total$discnumber=$tracktotal"
                        total=$((total + tracktotal))
                    else
                        return 0
                    fi
                fi
                if [ "$total" -ge "$file_count" ]; then
                    break
                fi
            done
            if [ $total -gt 0 ]; then
                echo "$total"
            fi
        )
}

media=
get_media_type() {
    if [ -z "$media" ]; then
        media="$tmed"
    fi
    if [ -n "$media" ]; then
        echo "$media"
    fi
}

year=
get_album_year() {
    if [ -z "$year" ]; then
        year="$originalyear"
    fi
    if [ -n "$year" ]; then
        echo "$year"
    fi
}

get_album_id() {
    album_id=
    if [ -n "$musicbrainz_album_id" ]; then
        album_id="$musicbrainz_album_id"
        echo "$album_id"
    else
        year="$(get_album_year)"
        album_id_string="${album_artist} ${album} ${compilation} ${year} ${tracktotal} ${disctotal}"
        if command -v md5sum >/dev/null 2>&1; then
            echo "$album_id_string" | md5
        else
            echo "$album_id_string" | md5
        fi
    fi
}

get_genre() {
    if [ -n "$albumgenre" ]; then
        genre="$albumgenre"
    fi
    if [ -n "$genre" ]; then
        # Sanitize / Improve consistency. Better plan: fix the tags
        lower_genre="$(echo "$genre" | tr '[:upper:]' '[:lower:]')"
        case "$lower_genre" in
            none | '' | miscellaneous | other | unclassifiable | hsh)
                genre=
                ;;
            soundtracks)
                genre=Soundtrack
                ;;
            videogame | video\ game* | vgm | game*)
                genre=Game
                ;;
            dance\ \&\ dj)
                genre=Dance
                ;;
            heavy\ metal)
                genre=Metal
                ;;
            holiday)
                genre=Christmas
                ;;
        esac
        base="$(basename "$(dirname "$1")")"
        if [ "$genre" != Game ] \
            && [ "$genre" != Soundtrack ] \
            && ([ -z "$2" ] || ! echo "$base" | grep -qEx "$2"); then
        if echo "$base" | grep -qi soundtrack \
            || echo "$base" | grep -qiw ost; then
        genre=Soundtrack
    elif echo "$releasetype" | tr '/,' '  ' | grep -qwi soundtrack; then
        echo >&2 "Warning: $1 has a soundtrack releasetype, but no Soundtrack genre"
    fi
fi
fi
if [ -z "$genre" ]; then
    genre=Unknown\ Genre
fi
echo "$genre"
}

sort_tracks() {
    if [ $# -eq 0 ]; then
        set -- 1 2n
    fi

    for i in $(seq 1 $#); do
        arg=$1
        shift
        argb="$(echo "$arg" | sed -e 's#[bdfingMr]*$##')"
        set -- "$@" -k"$argb,$arg"
    done

    sed -e 's#\(.*\)/\([^/]*\)$#\1	\2#' \
        | gsort -s -t"$TAB" "$@" \
        | uniq \
        | sed -e 's#\(.*\)	\([^	]*\)$#\1/\2#'
}

# shellcheck disable=SC2183
preparebar() {
# $1 - bar length
# $2 - bar char
    barlen=$1
    barspaces=$(printf "%*s" "$1")
    barchars=$(printf "%*s" "$1" | tr ' ' "${2:-#}")
}

# shellcheck disable=SC2183
setup_clearbar () {
    clearlen="$(tput cols)"
    clearspaces=$(printf "%*s" "$clearlen")
}
trap 'setup_clearbar' WINCH

clearbar() {
    printf "\\r$clearspaces\\r"
}

progressbar() {
# $1 - number (-1 for clearing the bar)
# $2 - max number
    if [ "$1" -eq -1 ]; then
        printf "\r  $barspaces\r"
    else
        barch=$(($1*barlen/$2))
        barsp=$((barlen-barch))
        printf "\r%s[%.${barch}s%.${barsp}s]%s\r" "${3:+$3 }" "$barchars" "$barspaces" "${4:+ $4}"
    fi
}

