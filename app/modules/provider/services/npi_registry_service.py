import httpx
import logging
from typing import Tuple, Optional
from fastapi import status, HTTPException

logger = logging.getLogger(__name__)

class NPIRegistryService:
    """
    Service to interact with the NPPES (National Plan and Provider Enumeration System) 
    API to verify healthcare provider credentials.
    """
    NPPES_URL = "https://npiregistry.cms.hhs.gov/api/"

    @staticmethod
    async def verify_npi_data(npi: str, first_name: str, last_name: str) -> Tuple[bool, str]:
        """
        Calls the NPPES API to verify:
        1. The NPI exists.
        2. The NPI status is 'Active'.
        3. The First and Last names match the registry.
        
        Returns: (is_valid: bool, message: str)
        """
        params = {
            "number": npi,
            "version": "2.1",
            "enumeration_type": "NPI-1"  # NPI-1 is for individual practitioners
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(NPIRegistryService.NPPES_URL, params=params)
                
                if response.status_code != 200:
                    logger.error(f"NPPES API returned status {response.status_code}")
                    return False, "NPI Registry is temporarily unavailable. Please try again later."

                data = response.json()
                # print("Response:", data)
                # 1. Check if any results were found
                if data.get("result_count", 0) == 0:
                    return False, "The provided NPI number was not found in the national registry."

                result = data["results"][0]
                basic_info = result.get("basic", {})

                # 2. Check for Active Status
                # 'A' = Active, 'D' = Deactivated
                npi_status = basic_info.get("status")
                if npi_status != "A":
                    return False, "This NPI number is currently deactivated in the national registry."

                # 3. Name Verification (Case-Insensitive)
                registry_first_name = basic_info.get("first_name", "").strip().upper()
                registry_last_name = basic_info.get("last_name", "").strip().upper()
                
                input_first_name = first_name.strip().upper()
                input_last_name = last_name.strip().upper()

                # We check if the input name is a match or a partial match (to handle middle names/initials)
                if registry_first_name != input_first_name or registry_last_name != input_last_name:
                    logger.warning(f"NPI Name Mismatch: Input({input_first_name} {input_last_name}) vs Registry({registry_first_name} {registry_last_name})")
                    return False, f"Name mismatch. The registry associated with this NPI is {registry_first_name} {registry_last_name}."

                return True, "NPI successfully verified."

            except httpx.RequestError as exc:
                logger.error(f"An error occurred while requesting {exc.request.url!r}: {exc}")
                return False, "Could not connect to the NPI verification service."
            except Exception as e:
                logger.error(f"Unexpected error in NPI verification: {str(e)}")
                return False, "An unexpected error occurred during NPI verification."