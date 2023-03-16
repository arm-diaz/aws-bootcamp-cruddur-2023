from datetime import datetime, timedelta, timezone
from opentelemetry import trace
import os

from libs.db import pool, query_wrap_array

if os.getenv("ENABLE_HONEYCOMB_LOG"):
    tracer = trace.get_tracer("home.activities")


class HomeActivities(object):
    
    @staticmethod
    def get_data(now, cognito_user_id):
        sql = query_wrap_array("""
                                SELECT
                                    activities.uuid,
                                    users.display_name,
                                    users.handle,
                                    activities.message,
                                    activities.replies_count,
                                    activities.reposts_count,
                                    activities.likes_count,
                                    activities.reply_to_activity_uuid,
                                    activities.expires_at,
                                    activities.created_at
                                FROM public.activities
                                LEFT JOIN public.users ON users.uuid = activities.user_uuid
                                ORDER BY activities.created_at DESC
        """)
        print(sql)

        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                # this will return a tuple
                # the first field being the data
                results = cur.fetchall()

        print(results)

        if cognito_user_id != None:
            extra_crud = {
                "uuid": "248959df-3079-4947-b847-9e0892d1bab4",
                "handle": "Lore",
                "message": "My dear brother, it is the humans that are the problem",
                "created_at": (now - timedelta(hours=1)).isoformat(),
                "expires_at": (now + timedelta(hours=12)).isoformat(),
                "likes": 1452,
                "replies": [],
            }
            results.append(extra_crud)

        return results

    def run(logger, request, xray_recorder, cognito_user_id=None):
        logger.info("Home Activities")
        now = datetime.now(timezone.utc).astimezone()

        if os.getenv("ENABLE_HONEYCOMB_LOG"):
            with tracer.start_as_current_span("home-activities-mock-data"):
                span = trace.get_current_span()
                span.set_attribute("app.now", now.isoformat())
                results = HomeActivities.get_data(now, cognito_user_id)
                span.set_attribute("app.result_length", len(results))
                return results
                
        elif os.getenv("ENABLE_CLOUDWATCH_LOG"):
            logger.info('Hello Cloudwatch! from  /api/activities/home')
            logger.info("home-activities-mock-data")
            logger.info(f"app.now: {now.isoformat()}")
            results = HomeActivities.get_data(now, cognito_user_id)
            logger.info(f"app.result_length: {len(results)}")
            return results

        elif os.getenv("ENABLE_XRAY_LOG"):
            segment = xray_recorder.begin_segment('home-activities')
            xray_time_dict = {
                "now": now.isoformat()
            }
            segment.put_annotation('now', str(xray_time_dict["now"]))
            segment.put_annotation('method', str(request.method))
            segment.put_annotation('url', str(request.url))

            segment.put_metadata('now', xray_time_dict, 'home-activities-now')
            segment.put_metadata('method', request.method, 'http')
            segment.put_metadata('url', request.url, 'http')

            subsegment = xray_recorder.begin_subsegment('home-activities-mock-data')

            results = HomeActivities.get_data(now, cognito_user_id)
            xray_results_size_dict = {
               "result-size": len(results)
            }
            
            subsegment.put_annotation('result_size', int(xray_results_size_dict["result-size"]))
            subsegment.put_metadata('result-size', xray_results_size_dict, 'home-activities-mock-data-results-size')

            xray_recorder.end_subsegment()
            #xray_recorder.end_segment()
            return results
        else:
            logger.info("No loggers are running")
            results = HomeActivities.get_data(now, cognito_user_id)
            return results
