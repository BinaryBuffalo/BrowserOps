import asyncio
from datetime import datetime
import json
from pathlib import Path
import sys
from playwright.async_api import async_playwright, Error as PlaywrightError

class BrowserMonitor:
    def __init__(
        self,
        sessions_dir='sessions',
        instances_file='instances.json',
        snapshots_dir='screenshots',
        screenshot_interval=10,
        proxy=None,
        user_agents_file='useragents.txt'
    ):
        self.sessions_dir = Path(sessions_dir)
        self.instances_file = self.sessions_dir / instances_file
        self.snapshots_dir = Path(snapshots_dir)
        self.screenshot_interval = screenshot_interval  # Interval in seconds
        self.proxy = proxy  # Proxy configuration
        self.user_agents_file = Path(user_agents_file)  # User agents file
        self.alive = True
        self.browser_closed_event = asyncio.Event()
        self.instance_number = None
        self.profile_path = None
        self.user_agent = None

    def read_instances(self):
        """Reads the instances.json file and returns the list of instances."""
        if not self.instances_file.exists():
            return []
        try:
            with open(self.instances_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def write_instances(self, instances):
        """Writes the list of instances to the instances.json file."""
        with open(self.instances_file, 'w') as f:
            json.dump(instances, f, indent=4)

    def assign_instance_number(self, instances):
        """Assigns the smallest available positive integer as the instance number."""
        existing_numbers = {instance['instance_number'] for instance in instances}
        i = 1
        while i in existing_numbers:
            i += 1
        return i

    def create_profile_directory(self, instance_number):
        """Creates a profile directory for the given instance number."""
        profile_dir = self.sessions_dir / f"profile_{instance_number}"
        profile_dir = profile_dir.resolve()
        print(f"Attempting to create profile directory: {profile_dir}")
        profile_dir.mkdir(parents=True, exist_ok=True)
        print(f"Profile directory successfully created: {profile_dir}")
        return profile_dir

    def pick_user_agent(self, instances):
        """Picks a user agent from useragents.txt that has not been used."""
        if not self.user_agents_file.exists():
            raise FileNotFoundError(f"{self.user_agents_file} does not exist.")
        
        with open(self.user_agents_file, 'r') as f:
            user_agents = [line.strip() for line in f.readlines() if line.strip()]
        
        used_agents = {instance['user_agent'] for instance in instances if 'user_agent' in instance}
        
        for user_agent in user_agents:
            if user_agent not in used_agents:
                return user_agent
        
        raise RuntimeError("No unused user agents available.")

    async def check_page_alive(self, page):
        """Attempts to evaluate a simple JavaScript expression on the page."""
        await page.evaluate("1 + 1")  # Simple JS evaluation

    async def monitor_browser(self, page):
        """Monitors the browser every 5 seconds to check if it's alive."""
        while self.alive:
            try:
                await asyncio.sleep(5)
                await self.check_page_alive(page)
            except PlaywrightError as e:
                if "closed" in str(e).lower():
                    print("exiting gracefully")
                    self.alive = False
                    self.browser_closed_event.set()
                    break
            except Exception:
                continue

    async def take_screenshots(self, page):
        """Takes screenshots at defined intervals and saves them to snapshots/ folder."""
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = self.snapshots_dir / f"user{self.instance_number}.png"
        while self.alive:
            try:
                await asyncio.sleep(self.screenshot_interval)
                await page.screenshot(path=str(screenshot_path))
            except Exception:
                continue

    async def execute_macro(self, page):
        """Monitors and executes actions from macro.txt or macro#.txt if they exist."""
        macro_file_global = Path('macro.txt')
        macro_file_instance = Path(f'macro{self.instance_number}.txt')
        executing = False
        chunk_counter = 0
        total_chunks = 0
        current_macro_file = None
        chunks = []
        macro_lock = asyncio.Lock()  # Ensure sequential execution

        while self.alive:
            if macro_file_instance.exists():
                selected_macro = macro_file_instance
            elif macro_file_global.exists():
                selected_macro = macro_file_global
            else:
                selected_macro = None

            if selected_macro and not executing:
                print(f"{selected_macro.name} detected")
                executing = True
                current_macro_file = selected_macro
                try:
                    with open(current_macro_file, 'r') as f:
                        content = f.read()
                    chunks = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]
                    total_chunks = len(chunks)
                    chunk_counter = 0
                except Exception as e:
                    print(f"Error reading macro file: {e}")
                    executing = False
                    current_macro_file = None
                    chunks = []
                    continue

            if executing and chunks:
                for chunk in chunks:
                    if not current_macro_file.exists():
                        print(f"{current_macro_file.name} deleted or renamed")
                        executing = False
                        break

                    chunk_counter += 1
                    print(f"Executing chunk [{chunk_counter}/{total_chunks}]")
                    try:
                        async with macro_lock:  # Ensure sequential execution
                            for line in chunk.split('\n'):
                                line = line.strip()
                                if line.startswith("actions.key_down"):
                                    key = line.split("('")[1].split("')")[0]
                                    print(f"Key Down: {key}")
                                    await page.keyboard.down(key)
                                elif line.startswith("actions.key_up"):
                                    key = line.split("('")[1].split("')")[0]
                                    print(f"Key Up: {key}")
                                    await page.keyboard.up(key)
                                elif line.startswith("time.sleep"):
                                    try:
                                        delay = float(line.split('(')[1].split(')')[0])
                                        print(f"Sleeping for {delay} seconds...")
                                        await asyncio.sleep(delay)  # Properly await the delay
                                    except ValueError:
                                        print(f"Invalid time.sleep value in macro: {line}")
                                elif line.startswith("actions.navigate"):
                                    url = line.split("('")[1].split("')")[0]
                                    print(f"Navigating to {url}")
                                    await page.goto(url)
                    except Exception as e:
                        print(f"Error executing macro chunk: {e}")
                        pass

                if executing:
                    chunk_counter = 0
            else:
                await asyncio.sleep(1)

    def handle_browser_close(self):
        """Handles the browser context closure."""
        if self.alive:
            print("exiting gracefully")
            self.alive = False
            self.browser_closed_event.set()

    def print_active_instances(self, instances):
        """Prints the list of active instances."""
        print("\nActive Instances:")
        for instance in sorted(instances, key=lambda x: x['instance_number']):
            print(f"Instance {instance['instance_number']}: {instance['profile_path']} (User Agent: {instance.get('user_agent', 'N/A')})")
        print("")  # Add an empty line for readability

    async def run(self):
        """Main coroutine to launch the browser, navigate to titleselector.html with query parameter, and start monitoring."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
    
        instances = self.read_instances()
        self.instance_number = self.assign_instance_number(instances)
        self.profile_path = self.create_profile_directory(self.instance_number)
        self.user_agent = self.pick_user_agent(instances)
    
        async with async_playwright() as p:
            # Configure browser launch options
            context_args = {
                'user_data_dir': str(self.profile_path),
                'headless': False,
                'viewport': {'width': 1920, 'height': 900},
                'args': ['--start-maximized', "--disable-infobars", "--disable-extensions"],
                'user_agent': self.user_agent
            }
    
            # Handle proxy configuration
            if self.proxy:
                context_args['proxy'] = {
                    "server": self.proxy.get("server"),
                }
                if self.proxy.get("username") and self.proxy.get("password"):
                    context_args['proxy']['username'] = self.proxy["username"]
                    context_args['proxy']['password'] = self.proxy["password"]
    
            context = await p.firefox.launch_persistent_context(**context_args)
    
            if context is None:
                print("Failed to launch persistent context.")
                print("exiting gracefully")
                return
    
            if not context.pages:
                page = await context.new_page()
            else:
                page = context.pages[0]
    
            html_file = Path('titleselector.html').resolve()
            if not html_file.exists():
                print(f"{html_file} does not exist.")
                print("exiting gracefully")
                return
            url = html_file.as_uri() + f"?title=user{self.instance_number}"
            try:
                await page.goto(url, timeout=60000)
            except PlaywrightError:
                pass
    
            context.on("close", self.handle_browser_close)
    
            instances.append({
                "instance_number": self.instance_number,
                "profile_path": str(self.profile_path),
                "user_agent": self.user_agent
            })
            self.write_instances(instances)
    
            print(f"Using profile {self.instance_number}")
            self.print_active_instances(instances)
    
            monitor_task = asyncio.create_task(self.monitor_browser(page))
            screenshot_task = asyncio.create_task(self.take_screenshots(page))
            macro_task = asyncio.create_task(self.execute_macro(page))
    
            await self.browser_closed_event.wait()
    
            instances = self.read_instances()
            instances = [instance for instance in instances if instance['instance_number'] != self.instance_number]
            self.write_instances(instances)
    
            monitor_task.cancel()
            screenshot_task.cancel()
            macro_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
            try:
                await screenshot_task
            except asyncio.CancelledError:
                pass
            try:
                await macro_task
            except asyncio.CancelledError:
                pass

    def start(self):
        """Starts the asynchronous event loop and runs the main coroutine."""
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            if self.instance_number is not None:
                instances = self.read_instances()
                instances = [instance for instance in instances if instance['instance_number'] != self.instance_number]
                self.write_instances(instances)
            print("exiting gracefully")

def parse_arguments():
    """Parses command-line arguments for proxy settings."""
    args = sys.argv[1:]
    if not args:
        return None  # No proxy, run normally
    elif len(args) == 2:
        return {"server": f"http://{args[0]}:{args[1]}"}
    elif len(args) == 4:
        return {"server": f"http://{args[0]}:{args[1]}", "username": args[2], "password": args[3]}
    else:
        print("Invalid arguments. Usage:")
        print("  python example.py IP PORT")
        print("  or")
        print("  python example.py IP PORT USERNAME PASSWORD")
        sys.exit(1)

if __name__ == "__main__":
    proxy_settings = parse_arguments()
    monitor = BrowserMonitor(proxy=proxy_settings)
    monitor.start()
