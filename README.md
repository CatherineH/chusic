# Catherine's scripts for music organization.

contains functionality for grabbing album covers off of xbox live music (Microsoft Groove) and google image search.
API keys are stored as environment variables.
Remember to get the client key for an application set up to use Groove for the 'BING_API_KEY', and the 'GOOGLE_API_KEY' needs to be set to the computer's current IP address.

## Recommended Ordering

Run add_missing_info to complete MP3 tags
Run add_images to grab either the internet image based on MP3 tags, or the thumbnail image in the folder. 
Finally, run reorganize_music last, as it removes any image files.