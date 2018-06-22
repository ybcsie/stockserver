import dataio
import msgopt
import tools
import datetime
import threading
import urllib.parse
import json


livedata_dict = {}
is_ready = False

listed_sid_path = "listed.sid"
trade_data_dir = "smd"
dtd_dir = "dtd"

months = 96


def main_loop():
    logger = msgopt.Logger("main", print)
    global is_ready
    while True:
        updated = True

        logger.logp("update_listed_list : start")
        dataio.update_listed_list(listed_sid_path)
        logger.logp("update_listed_list : done\n")

        dataio.update_all_dtd(dtd_dir, months)

        listed_id_list = dataio.get_stock_id_list(listed_sid_path)

        logger.logp("update_smd_in_list : start")
        force_update = False
        dataio.update_smd_in_list(listed_id_list, trade_data_dir, months, force_update)
        logger.logp("update_smd_in_list : done\n")

        dataio.update_livedata_dict(listed_id_list, livedata_dict)

        is_ready = True

        while True:
            now = datetime.datetime.now()

            if now.hour == 15 and not updated:
                break

            if not updated:
                dataio.update_livedata_dict(listed_id_list, livedata_dict)

            if 8 <= now.hour < 14:
                if updated:
                    updated = False
                continue

            # # debug
            # dataio.update_livedata_dict(listed_id_list, livedata_dict)
            # continue
            # # end debug

            logger.logp("sleep 300s ...\n")
            tools.delay(300)


def application(env, start_response):
    path_info = env.get("PATH_INFO")
    uwsgi_location = env.get("UWSGI_LOCATION")
    assert uwsgi_location is not None, "UWSGI_LOCATION is not defined in server setting"

    sub_dir = path_info.split(uwsgi_location + '/')[1]
    if is_ready:
        stat = "OK"
    else:
        stat = "LOADING"

    op_str = json.dumps({"stat": stat, "livedata": livedata_dict})
    # work_list = []
    # if sub_dir not in work_list:
    #     op_str = "{} is not defined".format(sub_dir)
    # else:
    #     query = env.get("QUERY_STRING")
    #     query = urllib.parse.parse_qs(query)
    #     delta_percentage_min_str = query.get("min")

    start_response("200 OK", [('Content-Type', 'text/html')])
    return [op_str.encode("utf-8")]


def debug_loop():
    while True:
        tools.delay(5)
        if is_ready:
            print(livedata_dict)


if __name__ != '__main__':
    threading.Thread(target=main_loop).start()

else:
    threading.Thread(target=main_loop).start()
    threading.Thread(target=debug_loop).start()