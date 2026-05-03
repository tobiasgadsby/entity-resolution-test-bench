import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import {styled} from "@mui/material/styles";
import {useMutation} from "@tanstack/react-query";
import axios, {AxiosError, type AxiosResponse} from "axios";

type props = {
    title: string;
    setFile: React.Dispatch<React.SetStateAction<any>>;
}

const VisuallyHiddenInput = styled('input')({
    clip: 'rect(0 0 0 0)',
    clipPath: 'inset(50%)',
    height: 1,
    overflow: 'hidden',
    position: 'absolute',
    bottom: 0,
    left: 0,
    whiteSpace: 'nowrap',
    width: 1,
    display: "flex",
    flex: 1
});

export default function FileInput({title, setFile}: props) {

    const uploadFile = useMutation<AxiosResponse, AxiosError, {event: any}>({
        mutationFn: ({event}) => {
            console.log(event)
            const file = event.target.files[0];
            console.log(file);
            setFile(file)
            return null;
        }
    })

    return <>
        <label className={"hover:cursor-pointer outline-2 outline-dashed rounded aspect-square bg-gray-300 flex flex-1 flex-col items-center justify-between"}>
            <div className="flex items-center justify-center h-1/2 m-2">
                <CloudUploadIcon sx={{ color: 'white' }} className={"!text-8xl"} />
            </div>
            <div className="flex items-center justify-center h-1/2">
                <h1>{title}</h1>
            </div>
            <VisuallyHiddenInput
            type="file"
            onChange={(event) => uploadFile.mutate({event})}
            multiple
            />
        </label>
        <VisuallyHiddenInput id="file-upload" type="file"/>
    </>
}