import {ExplainerTip} from "../Explainer/ExplainerDialog"

export const DataVizTips: ExplainerTip[] = [
    {
        title: "Energy Sources",
        text: "Bars above the line are energy sources coming in to your site, including grid imports (grey), solar generation (yellow) and your battery discharging. Each bar represents one half hour time window, and more yellow means you’re using more of your on-site solar.",
        media: {
            type: "video",
            src: "/dataviz/explain/energy_sources.mp4"
        }
    },
    {
        title: "Energy Consumers",
        text: "Bars below the line are consumers of energy, such as your heat pump (green), your usual electrical load (blue), any electricity you're exporting to the grid (grey) or charging your battery.",
        media: {
            type: "video",
            src: "/dataviz/explain/energy_consumers.mp4"
        }
    },
    {
        title: "Energy Storage",
        text: "Batteries will show up both below (charging) and above (discharging) the line in purple, including any inefficiencies in light purple",
        media: {
            type: "video",
            src: "/dataviz/explain/energy_storage.mp4"
        }
    },
    {
        title: "Energy Balance",
        text: "With everything included, your energy will be perfectly balanced above and below the line, showing where every kWh is coming from and where it's going to over the whole year.",
        media: {
            type: "video",
            src: "/dataviz/explain/energy_balance.mp4"
        }
    },
    {
        title: "Date Picker",
        text: "Use the date picker to select the starting date",
        media: {
            type: "video",
            src: "/dataviz/explain/date_picker.mp4"
        }
    },
    {
        title: "Time Duration",
        text: "Change the duration with the 'Days' dropdown.",
        media: {
            type: "video",
            src: "/dataviz/explain/time_duration.mp4"
        }
    },
    {
        title: "Time Scrolling",
        text: "The  ◀ ▶ buttons will scroll your view backwards and forwards one day. The << and >> buttons will scroll your view backwards and forwards one calendar month",
        media: {
            type: "video",
            src: "/dataviz/explain/time_scrolling.mp4"
        }
    },
    {
        title: "Mouseover",
        text: "Hover over a bar to see what it represents and how much energy was used in that time period.",
        media: {
            type: "video",
            src: "/dataviz/explain/mouseover.mp4"
        }
    },
]