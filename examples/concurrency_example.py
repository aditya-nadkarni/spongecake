import logging
import concurrent.futures
from datetime import date, timedelta
from time import sleep
from dotenv import load_dotenv
from spongecake import Desktop, AgentStatus
import subprocess

# Configure logging - most logs in the SDK are INFO level logs
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

load_dotenv()

# Map month number to month name
month_map = {'1': 'January', '2': 'February', '3': 'March', '4': 'April', '5': 'May', '6': 'June', '7': 'July', '8': 'August', '9': 'September', '10': 'October', '11': 'November', '12': 'December'}

def get_nth_weekend_dates(year, month, n):
    """
    Returns the day number (1-31) of the n-th Friday and n-th Sunday
    of the specified month and year.

    Example:
        If the n-th Friday is April 11, then the function returns (11, 13).
    """
    # Get the first day of the given month
    first_day = date(year, month, 1)
    # Calculate how many days until the first Friday
    offset_to_friday = (4 - first_day.weekday()) % 7
    nth_friday = first_day + timedelta(days=offset_to_friday + 7*(n-1))
    nth_sunday = nth_friday + timedelta(days=2)

    # If either the Friday or Sunday goes into the next month, return None, None
    if nth_friday.month != month or nth_sunday.month != month:
        return None, None

    # Return the day numbers (e.g., 11, 13) for the Friday and Sunday
    return nth_friday.day, nth_sunday.day


def check_flight_price(month, origin, destination, weekend_number):
    # Use local Docker container
    desktop_name = f"spongecake_weekend_flight_{weekend_number}"
    ## Best practice: When running desktops concurrently, its generally better to manage which ports each desktop will run on
    #   This avoids port conflicts. Spongecake will automatically handle port conflicts if needed, but this could lead to issues.
    # Set all ports based on weekend number (default port + weekend_number - 1)
    desktop = Desktop(
        name=desktop_name,
        vnc_port=5900 + weekend_number - 1,
        api_port=8000 + weekend_number - 1,
        marionette_port=3838 + weekend_number - 1,
        socat_port=2828 + weekend_number - 1
    )
    container = desktop.start()
    logging.info(f"🍰 Local Spongecake container started for weekend {weekend_number}: {container}")

    friday_date, sunday_date = get_nth_weekend_dates(2025, int(month), int(weekend_number))
    if friday_date is None or sunday_date is None:
        desktop.stop()
        logging.info(f"🍰 Local Spongecake container stopped for weekend: {weekend_number}")
        return None
    
    logging.info(f"Checking dates: {friday_date} - {sunday_date}")
    try:
        prompt = f'''First, navigate to: https://www.google.com/travel/flights
        On the Google flight home page click the origin field with a circle icon on the left hand side. Type in the origin location: {origin}, select the nearest airport. Click the destination field with a maps icon on the left hand side. Type in the destination location: {destination}, select the nearest airport. 
        Click on the departure field. A Calendar date-picker should open. Use the arrows on the left and ride hand side of the date picker container to find the given month: {month_map[month]}.

        Your task is to return the cheapest flight price for the given weekend of that month. You will need to find the cheapest flight for weekend number **{weekend_number}** in the month of {month_map[month]}. The dates of this weekend are {friday_date} - {sunday_date}.

        When selecting the weekend, you will see the days listed under the month as "S M T W Th F S" which represents the days of the week "Sunday Monday Tuesday Wednesday Thursday Friday Saturday". All the dates that fall under "F" are the dates for Fridays of the month. All the dates that fall under the last "S" are the dates for Saturdays of the month. And all the dates that fall under the first "S" are dates for Sundays of the month.
        Click on the "Departure" field, then click the Friday date: {friday_date}. Then click the Sunday date: {sunday_date}.

        Once the dates are selected, ensure you are looking at the correct Friday - Sunday. If the wrong days are selected, click on the "Departure" field again to select the right days.
        Once it looks correct, click the blue "Done" button on the bottom right corner of the date picker. 

        Finally, click the "Search" button in the middle. This should load a new page with a list of flights. Return the first flight price from the list (omit the dollar sign when applicable) (e.g. 231) - and NO OTHER TEXT.
        '''
            
        # Run the agent
        status, data = desktop.action(
            input_text=prompt,
            ignore_safety_and_input=True
        )

        if status == AgentStatus.COMPLETE:
            logging.info(f"✅ Task completed successfully for weekend {weekend_number}")
            return data.output_text
        elif status == AgentStatus.ERROR:
            error_msg = getattr(data, 'error_message', 'Unknown error')
            logging.error(f"Error processing weekend {weekend_number}: {error_msg}")
            return f"ERROR: {error_msg}"
        else:
            logging.warning(f"Unexpected status for weekend {weekend_number}: {status}")
            return f"UNKNOWN: Status {status}"
    except Exception as e:
        logging.error(f"Exception while checking weekend number {weekend_number}: {str(e)}")
        return f"EXCEPTION: {str(e)}"
    finally:
        desktop.stop()
        logging.info(f"🍰 Local Spongecake container stopped for weekend: {weekend_number}")

def main():
    # Prompt user for emails
    print('\n -> This is a flight price checker to find the cheapest set of flights for a weekend trip to a given destination. Provide the starting location, destination, and the month you want to travel to find the best weekend to fly')
    origin = input("\n>Starting location (Origin): ").strip()
    destination = input("\n>Destination: ").strip()
    month = input("\n>Month Number (e.g. 1 - January, 2 - February, ... 10 - October, etc.): ").strip()
    
    print(f"\nChecking best weekend to fly in {month_map[month]}...\n")

    weekends = [1, 2, 3, 4, 5]
    
    # Store results
    results = {}
    cheapest_weekend = float('inf')
    # Use ThreadPoolExecutor to run checks concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(weekends))) as executor:
        # Submit all checks and store the futures with their corresponding weekend numbers
        future_to_weekend = {executor.submit(check_flight_price, month, origin, destination, weekend): weekend for weekend in weekends}
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_weekend):
            weekend_number = future_to_weekend[future]
            try:
                result = future.result()
                if result is not None:
                    results[weekend_number] = result
                    try:
                        price = float(result)
                        if price < cheapest_weekend:
                            cheapest_weekend = price
                    except ValueError:
                        # Handle case where result is not a valid float (e.g., error message)
                        pass
                print(f"✓ Completed check for weekend {weekend_number}")
            except Exception as e:
                results[weekend_number] = f"ERROR: {str(e)}"
                print(f"✗ Error checking weekend {weekend_number}: {e}")
    
    print(f"\n----- Flight Prices for the month of {month_map[month]} -----")
    for weekend_number, result in results.items():
        print(f"    ✈️  Flight price for weekend number {weekend_number}: ${result}")
    print(f"\n💰  Cheapest weekend: ${cheapest_weekend}")
    print("\n🍰 All checks completed!")
    


if __name__ == "__main__":
    main()
