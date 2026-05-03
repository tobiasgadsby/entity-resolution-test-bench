import AddIcon from '@mui/icons-material/Add';
import * as React from "react";
import Menu from "@mui/material/Menu";
import {Button, MenuItem} from "@mui/material";
import {useMemo, useState} from "react";
import type {SkewedTechnique} from '../api.tsx';

export default function SkewedTechniqueSelector({ techniques, setTechniques }: SkewedTechnique) {

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [menuItems, setMenuitems] = useState<SkewedTechnique[]>([{'id': 'SWAP_CHAR', 'name': 'Character Swap'}, {'id': 'REMOVE_FIELD', 'name': 'Remove data from a field'}]);
    const open = Boolean(anchorEl);
    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = () => {
        setAnchorEl(null);
    }
    const handleSelect = (technique: SkewedTechnique) => {
        setAnchorEl(null);
        setTechniques([...techniques, technique]);
    }

    const excludeIds: Set<string> = new Set(techniques.map((technique: SkewedTechnique) => technique.id));
    // const menuList = useMemo(() => {
    //     excludeIds =
    //     return menuitems.filter((item) => !excludeIds.has(item.id));
    // }, [menuitems, techniques]);

    return (
    <div className={"outline-2 rounded overflow-scroll flex flex-1 flex-col"}>
        <div className={"outline-2 h-1/10 flex items-center justify-between p-1"}>
            <h1 className={""}>Skewed Technique Selector</h1>
            <button className={"flex items-center justify-center hover:cursor-pointer"} onClick={handleClick}>
                <AddIcon/>
            </button>
            <Menu
                id={"basic-menu"}
                anchorEl={anchorEl}
                open={open}
                onClose={handleClose}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'left',
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                }}
                slotProps={{
                    list: {
                        'aria-labelledby': 'button',
                    },
                }}
                >
                {menuItems.map((item: SkewedTechnique) => (
                    <MenuItem id={item.id} disabled={excludeIds?.has(item.id)} onClick={() => handleSelect(item)}>{item.name}</MenuItem>
                ))}

            </Menu>
        </div>
        {techniques?.map((technique) => (
            <div id={technique.id} className={"border border-t-0 border-x-0 p-1"}>{technique.name}</div>
        ))}
    </div>)
}