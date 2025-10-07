
export async function ensureNotify(){ try{ if(Notification && Notification.permission==='default'){ await Notification.requestPermission(); } }catch(e){} }
export function toastNote(title, body){ try{ if(Notification && Notification.permission==='granted'){ new Notification(title,{body}); } }catch(e){} }
