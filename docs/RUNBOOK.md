# TaskBoard Runbook

## Health checks
- `GET /health` returns `{"status":"ok"}` when the app and database are reachable.
- Returns **503** if the database can't be opened.

## Common issues

| Symptom | Check | Fix |
| --- | --- | --- |
| Container restarting | `docker logs taskboard` | Look for permission errors on `/data`; the volume must be writable by UID 10001 |
| `/health` returns 503 | Logs show `database unavailable` | Check the volume is mounted and has free space (`df -h`) |
| Pod stuck `Pending` | `kubectl -n taskboard describe pod <name>` | Usually the PVC can't bind; check `kubectl get pvc -n taskboard` |
| Pod `CrashLoopBackOff` | `kubectl -n taskboard logs <pod> --previous` | Read the last error before the crash |
| Pod `ImagePullBackOff` | `kubectl -n taskboard describe pod <name>` | Image name wrong, or GHCR package is private; make it public or add an imagePullSecret |
| Can't reach EC2 app | Security group and `terraform output` | Port 8000 must be open; check `sudo docker ps` on the instance |
| SSH times out | Your IP changed | Update `my_ip_cidr` in `terraform.tfvars` and re-apply |

## Useful commands
```bash
# Kubernetes
kubectl -n taskboard get pods,svc,pvc
kubectl -n taskboard logs deploy/taskboard -f
kubectl -n taskboard rollout restart deploy/taskboard
kubectl -n taskboard rollout status deploy/taskboard

# EC2
ssh -i taskboard-key.pem ec2-user@<public_ip>
sudo docker ps
sudo docker logs taskboard --tail 50
```

## Incident template (postmortem)
- **Summary:** what broke and the user impact
- **Timeline:** detection, response, resolution (with times)
- **Root cause:**
- **What went well / what didn't:**
- **Action items:** owner and due date for each fix
