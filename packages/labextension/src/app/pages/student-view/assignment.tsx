import React from "react";
import { NewAssignmentBadge } from "../../components/ui/badges";

export const Assignment = () => {

    return(
        <div>
            <h1>Assignment 1: hcduihweqd</h1>

            <div className="flex flex-col">
                <div className="flex flex-row">
                    <h6>Status</h6>
                    <NewAssignmentBadge/>
                </div>

                <div className="flex flex-row">
                    <h6>Deadline</h6>
                    <h6>10.10.2026 12:00:00</h6>
                </div>

                <div className="flex flex-row">
                    <h6>Max Points</h6>
                    <h6>800</h6>
                </div>
            </div>

            <h2>Notebook & files</h2>
        </div>
    );


}