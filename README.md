# NYC Open Data - 311 Service Requests Data Pipeline

A production-style batch ELT pipeline over New York City's 311 service request data built to handle the requirements real pipelines have; records update after they're loaded, reruns that are safe, and backfills across months of history.

<p align="center">
    <a href="https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2020-to-Present/erm2-nwe9/about_data" target="_blank">
        <img
            src="https://data.cityofnewyork.us/api/assets/3FF54443-CD9C-4E56-8A20-8D2BD245BD1A?nyclogo300.png"
            width="300"
            alt="NYC Open Data Logo"
        >
    </a>
</p>

## Why this dataset?

NYC311 is New York City’s official 24/7/365 non-emergency service. It lets residents and visitors access city government information, ask questions, and report neighborhood problems like potholes, noise, or missed trash collection.

Roughly 10,000 service requests are filed daily and many change status days later, which makes this a realistic stand-in for high-volume event data with late-arriving updates.
<br/>
<br/>

<hr>Code is MIT licensed. The 311 data itself belongs to NYC Open Data and is subject to their <a href="https://www.nyc.gov/main/terms-of-use"<span>terms of use</span></a>.
