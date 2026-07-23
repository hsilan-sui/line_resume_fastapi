// queue.js 範例
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

const { Queue, QueueEvents } = require('bullmq');
const IORedis = require('ioredis');

const REDIS_URL = process.env.REDIS_URL;
if (!REDIS_URL) {
  console.error("❌ REDIS_URL missing. Expect: rediss://default:PASSWORD@HOST:PORT");
  process.exit(1);
}

//自動判斷 TLS
const isTLS = REDIS_URL.startsWith("rediss://");

const baseOptions = {
  maxRetriesPerRequest: null, // BullMQ 建議
  enableReadyCheck: false,    // BullMQ 建議
  ...(isTLS ? { tls: {} } : {}),
};

const connection = new IORedis(REDIS_URL, baseOptions);
// QueueEvents 建議獨立連線
const eventsConnection = new IORedis(REDIS_URL, baseOptions);

const QUEUE_NAME = 'crawl';
const crawlQueue = new Queue(QUEUE_NAME, { connection });
const crawlEvents = new QueueEvents(QUEUE_NAME, { connection: eventsConnection });

async function closeAll() {
  await Promise.allSettled([
    crawlQueue.close(),
    crawlEvents.close(),
    connection.quit(),
    eventsConnection.quit(),
  ]);
}

module.exports = { crawlQueue, crawlEvents, connection, eventsConnection, QUEUE_NAME, closeAll };
