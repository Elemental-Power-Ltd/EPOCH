
export const submitConfig = async(config) => {
    try {
        const response = await fetch("/api/submit-config/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(config)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        return data;
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
        return data
    } catch (error) {
        console.error("Failed to get status:", error);
        return {"STATUS": "UNKNOWN"}
    }
}