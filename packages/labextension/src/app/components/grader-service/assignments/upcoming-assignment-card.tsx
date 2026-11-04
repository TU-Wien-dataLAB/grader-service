import React from "react";
import { Button } from "../../../shadcn-components/ui/button";
import { Card, CardAction, CardDescription, CardHeader, CardTitle } from "../../../shadcn-components/ui/card";
import { ChangesAssignmentBadge, NewAssignmentBadge } from "../../ui/badges";
import { CalendarX } from "lucide-react";
import { MoreTimeIcon } from "../../../../assets/more-time-icon";
import { getDeadlineParts } from "../../utils/deadline";
import { UpcomingAssignment } from "../../../../services/assignments.service";
import { Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { getFiles, lectureBasePath } from "../../../../services/local-file.service";


export const UpcomingAssignmentCard = ({ assignment }: { assignment: UpcomingAssignment } ) => {
  const deadline = getDeadlineParts(assignment.settings?.deadline);

  const { data: isAssignmentfetched } = useQuery({
    queryKey: ['filesStatus', assignment.lecture.id, assignment.id],
    queryFn: async () => {
        const files = await getFiles(`${lectureBasePath}${assignment.lecture?.code}/assignments/${assignment.id}`);
        return files?.length > 0;
    },
  }); 

  const badgeCase = () => {
      if (!isAssignmentfetched) {
          return <NewAssignmentBadge className="ml-2 shrink-0" />;
      } else if (false) {
          return <ChangesAssignmentBadge className="ml-2 shrink-0" />;
      }
  }

  return (
  <Card className="w-full bg-card p-4 flex flex-row flex-wrap gap-4 items-center">
    <div className="flex relative flex-col bg-background p-1.5 items-center justify-center shrink-0">
      {deadline ? (
        <>
          <h6 className="text-[#1E1E1E] font-semibold text-[14px]">{deadline.date}</h6>
          <h6 className="text-secondary-background text-[12px]">{deadline.time}</h6>
          {assignment.settings.late_submission &&
            <MoreTimeIcon className="absolute right-0 top-0 size-4 translate-x-1/2 -translate-y-1/2 text-primary"/>
          }
        </>
      ) : (
        <CalendarX className="text-[#1E1E1E] size-6 my-2 mx-3" />
      )
    }
    </div>
    <div className="flex flex-1 grow basis-48 min-w-0 flex-col justify-around">
      <CardHeader className="flex flex-row min-w-0 items-center p-0">
        <CardTitle className="min-w-0 truncate text-[16px]">
          {assignment.name}
        </CardTitle>
        {badgeCase()}
      </CardHeader>
      <CardDescription className="text-[12px] text-[#1E1E1E] py-1">
        {assignment.lecture.name}
      </CardDescription>
    </div>
    <CardAction className="self-center">
      <Link to={`/student/lectures/${assignment.lecture.id}/assignments/${assignment.id}`} className="block w-full">
        <Button className={'w-full cursor-pointer'}>
            Go to assignment
        </Button>
      </Link>
    </CardAction>
  </Card>
  
  );
}


