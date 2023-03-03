from datetime import datetime, timedelta, timezone
from opentelemetry import trace
import os

if os.getenv("ENABLE_HONEYCOMB_LOG"):
    tracer = trace.get_tracer("home.activities")


class HomeActivities(object):
    
    @staticmethod
    def get_data(now):
        results = [
            {
                "uuid": "68f126b0-1ceb-4a33-88be-d90fa7109eee",
                "handle": "Armando Diaz",
                "message": "Cloud is fun!",
                "created_at": (now - timedelta(days=2)).isoformat(),
                "expires_at": (now + timedelta(days=5)).isoformat(),
                "likes_count": 5,
                "replies_count": 1,
                "reposts_count": 0,
                "replies": [
                    {
                        "uuid": "26e12864-1c26-5c3a-9658-97a10f8fea67",
                        "reply_to_activity_uuid": "68f126b0-1ceb-4a33-88be-d90fa7109eee",
                        "handle": "Worf",
                        "message": "This post has no honor!",
                        "likes_count": 0,
                        "replies_count": 0,
                        "reposts_count": 0,
                        "created_at": (now - timedelta(days=2)).isoformat(),
                    }
                ],
            },
            {
                "uuid": "66e12864-8c26-4c3a-9658-95a10f8fea67",
                "handle": "Worf",
                "message": "I am out of prune juice",
                "created_at": (now - timedelta(days=7)).isoformat(),
                "expires_at": (now + timedelta(days=9)).isoformat(),
                "likes": 0,
                "replies": [],
            },
            {
                "uuid": "248959df-3079-4947-b847-9e0892d1bab4",
                "handle": "Garek",
                "message": "My dear doctor, I am just simple tailor",
                "created_at": (now - timedelta(hours=1)).isoformat(),
                "expires_at": (now + timedelta(hours=12)).isoformat(),
                "likes": 0,
                "replies": [],
            },
        ]
        return results

    def run(logger, request, xray_recorder):
        logger.info("Home Activities")
        now = datetime.now(timezone.utc).astimezone()

        if os.getenv("ENABLE_HONEYCOMB_LOG"):
            with tracer.start_as_current_span("home-activities-mock-data"):
                span = trace.get_current_span()
                span.set_attribute("app.now", now.isoformat())
                results = HomeActivities.get_data(now)
                span.set_attribute("app.result_length", len(results))
                return results
                
        elif os.getenv("ENABLE_CLOUDWATCH_LOG"):
            logger.info('Hello Cloudwatch! from  /api/activities/home')
            logger.info("home-activities-mock-data")
            logger.info(f"app.now: {now.isoformat()}")
            results = HomeActivities.get_data(now)
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

            results = HomeActivities.get_data(now)
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
            results = HomeActivities.get_data(now)
            return results
