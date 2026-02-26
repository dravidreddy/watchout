import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    scenarios: {
        baseline: {
            executor: 'constant-vus',
            vus: 10,
            duration: '5m'
        },
        load: {
            executor: 'constant-vus',
            vus: 100,
            duration: '15m',
            startTime: '5m'
        },
        stress: {
            executor: 'ramping-vus',
            stages: [
                { duration: '5m', target: 500 },
                { duration: '15m', target: 500 },
                { duration: '2m', target: 0 }
            ],
            startTime: '20m'
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<8000'], // 95% of requests must complete below 8s
        http_req_failed: ['rate<0.01'],    // Error rate must be < 1%
    },
};

export default function () {
    // SC5: k6 Load script targeting the core chat stream endpoint
    const url = `${__ENV.API_URL}/api/v1/chat/stream`;

    // Use a mock JWT / test bypass depending on environment
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${__ENV.TOKEN || 'test-bypass'}`
    };

    const payload = JSON.stringify({
        message: 'Plan a 3-day premium trip to Goa for 2 adults',
        trip_id: 'load_test_trip_' + __VU
    });

    const res = http.post(url, payload, { headers: headers });

    // Check that the request was accepted
    check(res, {
        'status is 200': (r) => r.status === 200,
    });

    sleep(1);
}
