import asyncio
import aiofiles
import aiohttp
import time
import argparse
import os

parser = argparse.ArgumentParser(usage="%(prog)s -u [PATH_TO_URL]",description="A simple command-line utility to check website HTTP status codes.")
parser.add_argument("-u", "--url", help="URL of the file to scan")
parser.add_argument("-o", "--output", help="Save the result here")
parser.add_argument("-r", "--retry", help="Number of times to retry if a task fails", default=2, type=int)
parser.add_argument("-c", "--concurrency", help="Number of tasks to run concurrently", default=10, type=int)
parser.add_argument("-t", "--timeout", help="Timeout in seconds for each task", default=20, type=int)
parser.add_argument("--no-redirect", help="Do not follow HTTP redirects (301, 302, etc)", action="store_true")
args = parser.parse_args()

if args.output:
    if not os.path.exists("result"):
        os.makedirs("result")

class Scanner:
    def __init__(self, file_path: str, retry: int = 2, concurrency: int = 10, timeout: int = 15, no_redirect: bool = False) -> None:
        self.file_path = file_path
        self.retry = retry
        self.concurrency = concurrency
        self.queue = asyncio.Queue()
        self.lock = asyncio.Lock()
        self.no_redirect = no_redirect
        self.semaphore = asyncio.Semaphore(concurrency)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.stats = {
            "[100-199]" : 0,
            "[200-299]" : 0,
            "[300-399]" : 0,
            "[400-499]" : 0,
            "[500-599]" : 0,
            "[ERROR]"   : 0,
            "[TIMEOUT]" : 0
        }

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

    def load_file(self) -> None:
        try:
            with open(self.file_path, 'r') as file:
                urls = list(dict.fromkeys(x.strip() for x in file if x.strip()))
            for url in urls:
                if not url.startswith(("https://", "http://")):
                    url = "https://" + url
                self.queue.put_nowait(url)
        except FileNotFoundError:
            print(f"{self.file_path} Not found.")
    
    async def fetch(self, session: aiohttp.ClientSession, url: str) -> None:
        for attempt in range(self.retry + 1):
            try:
                async with self.semaphore:
                    async with session.get(url, allow_redirects=not self.no_redirect) as r:
                        status = r.status

                if 100 <= status < 200:
                    async with self.lock:
                        self.stats['[100-199]'] += 1
                        print(f"[{status}] {url}")
                    return
                
                elif 200 <= status < 300:
                    async with self.lock:
                        self.stats['[200-299]'] += 1
                        print(f"[{status}] {url}")
                    if args.output:
                        async with aiofiles.open(f"result/{args.output}", 'a') as f:
                            await f.write(url + "\n")
                    return
                
                elif 300 <= status < 400:
                    async with self.lock:
                        self.stats['[300-399]'] += 1
                        print(f"[{status}] {url}")
                    return
                
                elif 400 <= status < 500:
                    async with self.lock:
                        self.stats['[400-499]'] += 1
                        print(f"[{status}] {url}")
                    return
                
                elif 500 <= status < 600:
                    if attempt < self.retry:
                        continue
                    async with self.lock:
                        self.stats['[500-599]'] += 1
                        print(f"[{status}] {url}")
                    return
                
            except (asyncio.TimeoutError, aiohttp.ServerTimeoutError):
                if attempt < self.retry:
                    continue

                async with self.lock:
                    self.stats['[TIMEOUT]'] += 1
                    print(f"[TIMEOUT] {url}")
                return
                
            except aiohttp.ClientError:
                if attempt < self.retry:
                    continue
                async with self.lock:
                    self.stats['[ERROR]'] += 1
                    print(f"[ERROR] {url}")
                return
                
    async def worker(self, session:aiohttp.ClientSession) -> None:
        try:
            while True:
                url = await self.queue.get()
                try:
                    await self.fetch(session, url)
                finally:
                    self.queue.task_done()
        except asyncio.CancelledError:
            raise


    async def run(self) -> None:
        self.load_file()

        if self.queue.empty():
            print(f"{self.file_path} Empty")
            return
        
        async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
            tasks = [asyncio.create_task(self.worker(session)) for _ in range(self.concurrency)]

            await self.queue.join()

            for t in tasks:
                t.cancel()

        print(f"\nRESULT : ")
        for key, value in self.stats.items():
            print(f"{key:<10} : {value}")

        if args.output:
            print(f"saved on result/{args.output}")

async def main() -> None:
    if not args.url:
        parser.print_help()
        return
    start_time = time.time()
    await Scanner(file_path=args.url, retry=args.retry, concurrency=args.concurrency, timeout=args.timeout, no_redirect=args.no_redirect).run()
    print(f"Total : {time.time() - start_time : .2f} Seconds")
if __name__ == "__main__":
    asyncio.run(main())
