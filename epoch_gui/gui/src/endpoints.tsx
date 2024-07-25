
export const submitOptimisationJob = async(payload) => {
    try {
        const response = await fetch("/api/submit-optimisation-job/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to submit configuration:", error);
    }
}

export const getStatus = async() => {
    try {
        const response = await fetch("/api/get-status");

        if(!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log(data);
        return data
    } catch (error) {
        console.error("Failed to get status:", error);
        return {"STATUS": "UNKNOWN"}
    }
}